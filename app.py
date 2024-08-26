from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

SOURCE_PATH = os.path.join(os.getcwd(), 'source_code')

@app.route('/')
def index():
    with open(os.path.join(SOURCE_PATH, 'code.py'), 'r') as py_file:
        python_code = py_file.read()

    with open(os.path.join(SOURCE_PATH, 'code1.c'), 'r') as c_file:
        c_code = c_file.read()

    return render_template('index.html', python_code=python_code, c_code=c_code)

@app.route('/run_python_code', methods=['POST'])
def run_python_code():
    try:
        output = subprocess.check_output(['python', os.path.join(SOURCE_PATH, 'code.py')],
                                         stderr=subprocess.STDOUT,
                                         universal_newlines=True)
        return jsonify({'output': output})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.output})

@app.route('/run_c_code', methods=['POST'])
def run_c_code():
    try:
        subprocess.check_output(['gcc', os.path.join(SOURCE_PATH, 'code.c'), '-o', 'code.out'],
                                stderr=subprocess.STDOUT)
        output = subprocess.check_output(['./code.out'], stderr=subprocess.STDOUT, universal_newlines=True)
        return jsonify({'output': output})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.output})

if __name__ == '__main__':
    app.run(debug=True)
