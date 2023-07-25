import os
import subprocess
import logging
import re
from flask import Flask, render_template, request

app = Flask(__name__)

# Create a directory to store log files
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# Counter to keep track of the current step
current_step = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_lilypad', methods=['POST'])
def run_lilypad():
    data = request.get_json()
    template = data.get('template')
    params = data.get('params')

    # Construct the Lilypad command
    command = f"lilypad run --template {template} --params \"{params}\""

    try:
        # Execute the Lilypad command and capture real-time output
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Create a log file for this set of parameters
        log_file = os.path.join(log_dir, f"params_{params}.log")

        # Read the real-time output and save it to the log file
        with open(log_file, 'w') as log:
            for line in process.stdout:
                # Check if it's a new step
                step_match = re.match(r'\d+', line)
                if step_match:
                    step = int(step_match.group(0))
                    if step != current_step:
                        current_step = step
                        log.write(f"Step {step}:\n")
                log.write(line)

        # Wait for the command to complete
        process.wait()

        # Read the log file to extract the final IPFS link
        ipfs_link = extract_ipfs_link(log_file)

        if ipfs_link:
            image_link = f"{ipfs_link}/outputs/image0.png"
            return {'ipfs_link': ipfs_link, 'image_link': image_link}, 200
        else:
            return {'error': 'IPFS link not found or does not have a 46-character CID'}, 400

    except subprocess.CalledProcessError as e:
        error_msg = str(e)
        return {'error': error_msg}, 400

def extract_ipfs_link(log_file):
    # Read the log file to extract the final IPFS link with a 46-character CID
    with open(log_file, 'r') as log:
        log_content = log.read()
        match = re.search(r'https://ipfs.io/ipfs/\S{46}', log_content)
        if match:
            return match.group(0)
    return None

if __name__ == '__main__':
    app.run(debug=True)
