import subprocess
import tempfile
import os

def run_python_code(code):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as py_file:
        py_file.write(code.encode('utf-8'))
        py_file.flush()
        py_file.close()
        
        try:
            result = subprocess.run(['python', py_file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        finally:
            # Очистка
            os.remove(py_file.name)
    
    return output
