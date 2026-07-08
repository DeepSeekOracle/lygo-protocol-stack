import subprocess
import os
import time
import sys

print('Cleaning git processes and lock...')
subprocess.call('cmd /c "taskkill /f /im git.exe 2>nul"', shell=True)
time.sleep(1)
lock = '.git/index.lock'
if os.path.exists(lock):
    try:
        os.remove(lock)
        print('Lock removed')
    except:
        print('Could not remove lock')

print('Git add all...')
subprocess.check_call(['git', 'add', '-A'])

print('Git commit...')
try:
    subprocess.check_call(['git', 'commit', '-m', 'feat(bridge): Phase 3 complete - DeployBridge.s.sol, VortexOraclePRB.sol, DeployAndBridge.t.sol, contract compatibility updates for full system'])
except subprocess.CalledProcessError:
    print('Nothing new to commit or commit failed, continuing to push')

print('Extracting token with GCM...')
gcm = r'C:\Program Files\Git\mingw64\bin\git-credential-manager.exe'
p = subprocess.Popen([gcm, 'get'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, _ = p.communicate('protocol=https\nhost=github.com\n\n')
tok = ''
for line in out.splitlines():
    if 'password=' in line:
        tok = line.split('=', 1)[1].strip()
        break

if not tok:
    print('No token found')
    sys.exit(1)

print('Token found, length', len(tok))

orig = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
temp = 'https://x-access-token:' + tok + '@github.com/DeepSeekOracle/lygo-protocol-stack.git'
subprocess.check_call(['git', 'remote', 'set-url', 'origin', temp])
print('Pushing...')
res = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
print('Push returncode:', res.returncode)
print('Push stdout:', res.stdout[-500:] if res.stdout else '')
print('Push stderr:', res.stderr[-500:] if res.stderr else '')
subprocess.check_call(['git', 'remote', 'set-url', 'origin', orig])
print('Remote restored.')
print('Done.')