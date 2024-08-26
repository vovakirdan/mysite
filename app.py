from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Path to the source code files
SOURCE_PATH = os.path.join(os.getcwd(), 'source_code')

@app.route('/')
def index():
    return render_template('index.html')

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
        # Compile the C code
        subprocess.check_output(['gcc', os.path.join(SOURCE_PATH, 'code.c'), '-o', 'code.out'],
                                stderr=subprocess.STDOUT)
        # Run the compiled C code
        output = subprocess.check_output(['./code.out'], stderr=subprocess.STDOUT, universal_newlines=True)
        return jsonify({'output': output})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.output})

if __name__ == '__main__':
    app.run(debug=True)
