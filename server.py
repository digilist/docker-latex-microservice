#!/usr/bin/env python3.5
from http.server import BaseHTTPRequestHandler, HTTPServer
import tempfile
import subprocess
import json
import base64
import os

class CompilationFailedException(Exception):
    '''Exception will be thrown when compilation of tex source fails'''

class TexCompiler():
    def __init__(self, compiler):
        self.compiler = compiler
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tex_file_path = self.tmpdir.name + '/main.tex'
        self.pdf_file_path = self.tmpdir.name + '/main.pdf'

    def compile(self, tex_source: str):
        print('compiling ' + self.compiler)

        # Write tex source into file
        self.write_file('main.tex', tex_source);

        # Compile pdf
        cmd = self.compiler + ' -interaction=nonstopmode main.tex'
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, cwd=self.tmpdir.name)
        output = process.communicate()

        if process.returncode != 0:
            # An error occured during latex compilation
            raise CompilationFailedException(output)
        
        # Load pdf
        try:
            pdf_handle = open(self.pdf_file_path, 'rb')
            pdf = pdf_handle.read()
            pdf_handle.close()
        except FileNotFoundError:
            raise CompilationFailedException(output)

        return output, pdf

    def add_files(self, files):
        for filename, content in files.items():
            self.write_file(filename, base64.b64decode(content))

    def write_file(self, filepath: str, content: bytes):
        '''Write file relative to tmp directory'''
        dirname = os.path.dirname(filepath)
        if dirname != '':
            # if the path contains subdirectories, create them
            os.makedirs(self.tmpdir.name + '/' + dirname, exist_ok=True)

        file_handle = open(self.tmpdir.name + '/' + filepath, 'wb')
        file_handle.write(content)
        file_handle.close()


class ServerHandler(BaseHTTPRequestHandler):
    compilers = [
        'tex',
        'latex',
        'pdftex',
        'pdflatex',
        'xetex',
        'xelatex',
        'luatex',
        'lualatex'
    ]

    def do_POST(self):
        tex_compiler = self.path.replace('/', '')
        if tex_compiler == '':
            tex_compiler = 'pdflatex'

        if not tex_compiler in self.compilers:
            self.write_json({
                'status': 'error',
                'message': 'Invalid compiler. Valid compilers are: ' + str(self.compilers),
            }, 400)
            return

        print('Incoming ' + tex_compiler + ' request')

        if 'content-length' not in self.headers:
            self.write_json({
                'status': 'error',
                'message': 'Content-Length header not provided',
            })
            return


        content_len = int(self.headers['content-length'])
        post_content_type = self.headers['content-type']
        post_body = self.rfile.read(content_len)

        try:
            compiler = TexCompiler(tex_compiler)
            if (post_content_type == 'application/json'):
                data = json.loads(post_body.decode())
                if not 'tex_source' in data:
                    self.write_json({
                        'status': 'error',
                        'message': 'You need to pass a tex_source',
                    }, 400)
                    return

                if 'files' in data:
                    compiler.add_files(data['files'])

                compiler_output, pdf = compiler.compile(bytes(data['tex_source'], 'utf-8'))
            else:
                compiler_output, pdf = compiler.compile(post_body)

            if (self.headers['accept'] == 'application/json'):
                self.write_json({
                    'status': 'success',
                    'pdf': str(base64.b64encode(pdf)),
                    'compiler_output': str(compiler_output)
                })
                return

            self.write_pdf(pdf)
        except CompilationFailedException as error:
            self.write_json({
                'status': 'error',
                'compiler_output': str(error)
            }, 500)

    def send_headers(self, status_code: int, content_type: str = 'application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def write_json(self, data, status_code: int = 200):
        self.send_headers(status_code)
        self.wfile.write(bytes(json.dumps(data, indent=4), 'utf-8'))

    def write_pdf(self, pdf: bytes):
        self.send_headers(200, 'application/pdf')
        self.wfile.write(pdf)


def run(server_class=HTTPServer, handler_class=ServerHandler, port=7000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

if __name__ == '__main__':
    from sys import argv

    run()