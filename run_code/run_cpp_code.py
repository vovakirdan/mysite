import subprocess
import os
import tempfile

def run_cpp_code(code):
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False) as cpp_file:
        cpp_file.write(code.encode('utf-8'))
        cpp_file.flush()
        cpp_file.close()
        
        executable = cpp_file.name.replace('.cpp', '')
        try:
            # Компиляция
            subprocess.run(['g++', cpp_file.name, '-o', executable], check=True)
            # Выполнение
            result = subprocess.run([executable], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        except subprocess.CalledProcessError as e:
            output = e.stderr.decode('utf-8')
        finally:
            # Очистка
            os.remove(cpp_file.name)
            if os.path.exists(executable):
                os.remove(executable)
    
    return output
