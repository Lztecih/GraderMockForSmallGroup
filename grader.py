import subprocess
import os
import glob
import time
import re

def run_grader(submission_file, problem_id, language):
    current_dir = os.getcwd()
    problem_dir = f"problems/{problem_id}"

    time_limit = 1.0  
    mem_limit_mb = 256 
    
    limits_file = f"{problem_dir}/limits.txt"
    if os.path.exists(limits_file):
        with open(limits_file, "r") as f:
            lines = f.read().splitlines()
            if len(lines) >= 1: time_limit = float(lines[0])
            if len(lines) >= 2: mem_limit_mb = int(lines[1])

    compiler = "g++" if language == "cpp" else "gcc"
    compile_cmd = [
        "docker", "run", "--rm", 
        "-v", f"{current_dir}:/app", 
        "-w", "/app",
        "cpp-sandbox", 
        compiler, f"submissions/{submission_file}", "-o", "temp/exec"
    ]
    
    try:
        compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
        if compile_res.returncode != 0:
            return "Compilation Error (CE)", 0, "X", [{"num": "-", "time": "-", "result": "Compilation Error", "char": "X", "msg": compile_res.stderr}]
    except Exception as e:
        return "System Error", 0, "E", [{"num": "-", "time": "-", "result": "Docker Failed", "char": "E", "msg": str(e)}]

    input_files = glob.glob(f"{problem_dir}/*.in")
    
    if not input_files:
        return "System Error", 0, "E", []

    def get_test_num(filepath):
        filename = os.path.basename(filepath)
        numbers = re.findall(r'\d+', filename)
        return int(numbers[-1]) if numbers else 0
        
    input_files.sort(key=get_test_num)
    
    total_cases = len(input_files)
    passed_cases = 0
    summary_string = ""  
    
    test_results = [] 

    for i, in_filepath in enumerate(input_files, start=1):
        out_filepath = in_filepath[:-3] + ".sol"
        
        if not os.path.exists(out_filepath):
            test_results.append({'num': i, 'time': 'N/A', 'result': 'Missing .sol File', 'char': 'E'})
            summary_string += "E"
            continue

        try:
            # We removed the "time" wrapper. It now just runs the executable directly and safely!
            run_cmd = [
                "docker", "run", "--rm", "-i", 
                f"--memory={mem_limit_mb}m", 
                "-v", f"{current_dir}:/app", 
                "-w", "/app",
                "cpp-sandbox", 
                "./temp/exec"
            ]
            
            with open(in_filepath, "r") as f_in:
                start_time = time.perf_counter()
                
                # Give Docker a tiny bit of extra time to boot up before Python cuts it off
                run_res = subprocess.run(run_cmd, stdin=f_in, capture_output=True, text=True, timeout=time_limit + 0.5)
                
                host_time = time.perf_counter() - start_time

            # Calculate the pure C++ execution time by subtracting the 0.18s Docker boot tax
            pure_execution_time = max(0.001, host_time - 0.180)
            time_str = f"{pure_execution_time:.3f}s"

            # Check for Time Limit manually
            if pure_execution_time > time_limit:
                test_results.append({'num': i, 'time': time_str, 'result': 'Time Limit Exceeded', 'char': 'T'})
                summary_string += "T"
                continue

            with open(out_filepath, "r") as f_out:
                expected = f_out.read().strip()
                actual = run_res.stdout.strip()
                
                if run_res.returncode == 137:
                    test_results.append({'num': i, 'time': time_str, 'result': 'Memory Limit Exceeded', 'char': 'T'})
                    summary_string += "T"
                elif run_res.returncode != 0:
                    # Capture the actual error message so we aren't guessing anymore!
                    err_msg = run_res.stderr.strip() if run_res.stderr else f"Exit Code {run_res.returncode}"
                    # Truncate it if it's too long for the table
                    short_err = (err_msg[:25] + '..') if len(err_msg) > 25 else err_msg
                    test_results.append({'num': i, 'time': time_str, 'result': f'RE: {short_err}', 'char': '-'})
                    summary_string += "-"
                elif actual == expected:
                    passed_cases += 1
                    test_results.append({'num': i, 'time': time_str, 'result': 'Correct', 'char': 'P'})
                    summary_string += "P"
                else:
                    test_results.append({'num': i, 'time': time_str, 'result': 'Wrong Answer', 'char': '-'})
                    summary_string += "-"

        except subprocess.TimeoutExpired:
            test_results.append({'num': i, 'time': f"> {time_limit}s", 'result': 'Time Limit Exceeded', 'char': 'T'})
            summary_string += "T"
        except Exception as e:
            test_results.append({'num': i, 'time': 'N/A', 'result': 'System Error', 'char': 'E'})
            summary_string += "E"

    score = int((passed_cases / total_cases) * 100) if total_cases > 0 else 0
    status = "Accepted (AC)" if score == 100 else ("Partial Score" if score > 0 else "Wrong Answer (WA)")
    
    return status, score, summary_string, test_results