import subprocess
import os
import tempfile

def run_c_code(code):
    with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as c_file:
        c_file.write(code.encode('utf-8'))
        c_file.flush()
        c_file.close()
        
        executable = c_file.name.replace('.c', '')
        try:
            # Компиляция
            subprocess.run(['gcc', c_file.name, '-o', executable], check=True)
            # Выполнение
            result = subprocess.run([executable], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')
        except subprocess.CalledProcessError as e:
            output = e.stderr.decode('utf-8')
        finally:
            # Очистка
            os.remove(c_file.name)
            if os.path.exists(executable):
                os.remove(executable)
    
    return output
