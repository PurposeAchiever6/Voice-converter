"""
Simple test to generate real API output file
"""
import requests
import time
import json

def test_api_real_output():
    """Test the API with real file to generate actual output"""
    
    test_file = 'tests/1.leo test 8.28.wav'
    
    print('Testing API with real file to generate output...')
    print(f'Using: {test_file}')
    
    try:
        # Upload file
        with open(test_file, 'rb') as f:
            files = {'file': ('1.leo test 8.28.wav', f, 'audio/wav')}
            data = {'continuous_with_spaces': 'true'}
            
            print(f'Uploading with continuous_with_spaces=true mode...')
            response = requests.post('http://localhost:8000/upload', files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result['job_id']
            print(f'Upload successful! Job ID: {job_id}')
            
            # Check status multiple times
            for i in range(10):
                time.sleep(3)
                status_resp = requests.get(f'http://localhost:8000/status/{job_id}')
                if status_resp.status_code == 200:
                    status = status_resp.json()
                    print(f'   Status: {status["status"]} - {status["progress"]}% - {status["message"]}')
                    
                    if status['status'] == 'completed':
                        print(f'Job completed! Download URL: {status.get("download_url", "N/A")}')
                        
                        # Try to download the file
                        download_resp = requests.get(f'http://localhost:8000/download/{job_id}')
                        if download_resp.status_code == 200:
                            output_file = f'api_test_output_{job_id}.wav'
                            with open(output_file, 'wb') as f:
                                f.write(download_resp.content)
                            print(f'Output file saved: {output_file}')
                            print(f'File size: {len(download_resp.content):,} bytes')
                            return output_file
                        else:
                            print(f'Download failed: {download_resp.status_code}')
                        break
                    elif status['status'] == 'failed':
                        print(f'Job failed: {status.get("error", "Unknown error")}')
                        break
                else:
                    print(f'Status check failed: {status_resp.status_code}')
                    break
        else:
            print(f'Upload failed: {response.status_code} - {response.text}')
            
    except Exception as e:
        print(f'Test failed: {e}')
        return None

if __name__ == "__main__":
    output_file = test_api_real_output()
    if output_file:
        print(f'\nSuccess! Real API output file generated: {output_file}')
    else:
        print('\nFailed to generate API output file')
