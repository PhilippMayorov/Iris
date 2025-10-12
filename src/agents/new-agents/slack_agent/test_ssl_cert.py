#!/usr/bin/env python3
"""
Test script to verify SSL certificate creation for Slack OAuth HTTPS server
"""

import os
import sys
import ssl
import socket
import ipaddress
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def test_ssl_cert_creation():
    """Test SSL certificate creation"""
    print("🔐 Testing SSL certificate creation...")
    
    cert_file = "test_localhost.crt"
    key_file = "test_localhost.key"
    
    try:
        # Generate private key
        print("   Creating private key...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        print("   Creating certificate...")
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Dev"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Slack Agent Dev"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate to file
        print("   Writing certificate file...")
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key to file
        print("   Writing private key file...")
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ SSL certificate created successfully!")
        print(f"   Certificate: {cert_file}")
        print(f"   Private key: {key_file}")
        
        # Test loading the certificate
        print("   Testing certificate loading...")
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_file, key_file)
        print("✅ SSL certificate loads successfully!")
        
        # Clean up test files
        os.remove(cert_file)
        os.remove(key_file)
        print("✅ Test files cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ SSL certificate creation failed: {e}")
        # Clean up on error
        for file in [cert_file, key_file]:
            if os.path.exists(file):
                os.remove(file)
        return False

if __name__ == "__main__":
    print("🧪 Testing Slack OAuth HTTPS SSL Certificate Creation")
    print("=" * 60)
    
    success = test_ssl_cert_creation()
    
    if success:
        print("\n🎉 SUCCESS: SSL certificate creation is working!")
        print("   The setup script should now work with HTTPS OAuth.")
    else:
        print("\n❌ FAILED: SSL certificate creation needs debugging.")
        sys.exit(1)