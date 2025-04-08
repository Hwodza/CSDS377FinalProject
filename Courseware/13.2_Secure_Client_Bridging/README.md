# Secure Client Bridging

Now that we've created all of our certificates and keys, let's secure bridging between LAMPI and the EC2 instance by installing the certificates and keys, and reconfiguring our services. 

We have some keys on our host machine we need to get over to the lamp. We'll use secure copy, `scp`, to copy files to our remote machines. For Windows users the easiest path is probably to use `Git Shell` installed with [GitHub Desktop](https://desktop.github.com/). 

## LAMPI Setup

First we need to get our client public and private key over to the lamp, as well as the CA's public key. On your lamp, let's create a folder to hold the ssl\_keys. On your lamp, run:

```bash
lamp$ mkdir ~/ssl_keys
```

Note that for the rest of this excercise, we assume that your keys are named "b827eb74663e_broker". Replace this with the name of the credentials you created in the previous exercise. From your host, run:

```bash
host$ scp ~/ssl_keys/lampi_ca.crt pi@{lamp_ip_address}:/home/pi/ssl_keys/
host$ scp ~/ssl_keys/b827eb74663e_broker.crt pi@{lamp_ip_address}:/home/pi/ssl_keys/
host$ scp ~/ssl_keys/b827eb74663e_broker.key pi@{lamp_ip_address}:/home/pi/ssl_keys/
```

Now that the keys are on our lamp, we need to use `sudo` to get them into the appropriate folders for Mosquitto. Remote into your lamp and run:

```bash
lamp$ cd ~/ssl_keys
lamp$ sudo cp lampi_ca.crt /etc/mosquitto/ca_certificates/
lamp$ sudo cp b827eb74663e_broker.crt /etc/mosquitto/certs/
lamp$ sudo cp b827eb74663e_broker.key /etc/mosquitto/certs/
```

Now we'll update our Mosquitto config to use these credentials. Open **/etc/mosquitto/conf.d/lampi\_bridge.conf** in your text editor of choice.

We will change the port number to be **8883** the [IANA assigned port number for secure MQTT](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=mqtt).

Update the file:

* Update/Verify the bridge address is the FQDN of the server we found in the previous secdtion. Note that the port number is also specified.
* Add `bridge_cafile`,  `bridge_certfile`, `bridge_keyfile`, and `bridge_tls_version`.  See [Mosquitto Configuration](https://mosquitto.org/man/mosquitto-conf-5.html) for more information on these configuration parameters.

Note: once you start using certificates, you will need to consistently use FQDNs and not IP addresses (the IP address will not match the CN in the Certificate, leading to security warnings/failures).

Here's an example of a modified conf file:

```
connection b827eb74663e_broker
address ec2-52-20-29-213.compute-1.amazonaws.com:8883

remote_clientid b827eb74663e_broker
bridge_cafile /etc/mosquitto/ca_certificates/lampi_ca.crt
bridge_certfile /etc/mosquitto/certs/b827eb74663e_broker.crt
bridge_keyfile /etc/mosquitto/certs/b827eb74663e_broker.key
bridge_tls_version tlsv1.2

topic lamp/set_config in 1 "" devices/b827eb74663e/
topic lamp/changed out 1 "" devices/b827eb74663e/
topic lamp/connection/+/state out 2 "" devices/b827eb74663e/
topic lamp/associated in 2 "" devices/b827eb74663e/
cleansession false
```


## EC2 Setup

SSH to your EC2 instance and create a folder to hold your SSL keys.

```bash
cloud$ mkdir ~/ssl_keys
```

Similar to LAMPI Setup above, copy the **lampi_ca.crt**, **lampi_server.crt**, and **lampi_server.key** files to the **~/ssl\_keys** directory using `scp`.

Log back into your EC2 instance and copy the keys where they need to go:

```bash
cloud$ cd ~/ssl_keys
cloud$ sudo cp lampi_ca.crt /etc/mosquitto/ca_certificates/
cloud$ sudo cp lampi_server.crt /etc/mosquitto/certs/
cloud$ sudo cp lampi_server.key /etc/mosquitto/certs/
```

Finally, edit **/etc/mosquitto/conf.d/port.conf**: 

```
listener 8883 0.0.0.0
cafile /etc/mosquitto/ca_certificates/lampi_ca.crt
certfile /etc/mosquitto/certs/lampi_server.crt
keyfile /etc/mosquitto/certs/lampi_server.key
tls_version tlsv1.2
require_certificate true
use_identity_as_username true


listener 50002 0.0.0.0
protocol websockets
cafile /etc/mosquitto/ca_certificates/lampi_ca.crt
certfile /etc/mosquitto/certs/lampi_server.crt
keyfile /etc/mosquitto/certs/lampi_server.key
tls_version tlsv1.2

listener 1883 127.0.0.1
```
See [Mosquitto Configuration](https://mosquitto.org/man/mosquitto-conf-5.html) for more information on these configuration parameters.

For each _listener_ we specify the security configuration.  We have 3 listeners, 2 secure (MQTT on 8883 and MQTT Websockets on 50002) and 1 insecure (MQTT on port 1883, limited to localhost access).

Note that we are forcing the use of a certificate (```require_certificate true```) and also using the certificate identity as the username (```use_identity_as_username true```) (which is why we entered something like **b827eb74663e_broker** when we made the certificate). 

```bash
cloud$ sudo service mosquitto restart
lamp$ sudo service mosquitto restart
```

## Testing

You can use OpenSSL to test the operation of a secure connection to your Mosquitto Broker (just like your LAMPI Mosquitto Broker will connect) like so:

```bash
openssl s_client -connect {FQDN}:8883 -CAfile lampi_ca.crt
```


Example, with a FQDN of `ec2-54-82-61-44.compute-1.amazonaws.com`

```bash

openssl s_client -connect ec2-54-82-61-44.compute-1.amazonaws.com:8883 -CAfile lampi_ca.crt
CONNECTED(00000005)
depth=1 C = US, ST = OH, L = Cleveland, O = LAMPI, OU = LAMPI, CN = lampi, emailAddress = nick@barendt.com
verify return:1
depth=0 C = US, ST = Ohio, L = Cleveland, O = CWRU, CN = ec2-54-82-61-44.compute-1.amazonaws.com, emailAddress = nab2@cwru.edu
verify return:1
4342679084:error:14020410:SSL routines:CONNECT_CR_SESSION_TICKET:sslv3 alert handshake failure:/AppleInternal/Library/BuildRoots/66382bca-8bca-11ec-aade-6613bcf0e2ee/Library/Caches/com.apple.xbs/Sources/libressl/libressl-2.8/ssl/ssl_pkt.c:1200:SSL alert number 40
4342679084:error:140200E5:SSL routines:CONNECT_CR_SESSION_TICKET:ssl handshake failure:/AppleInternal/Library/BuildRoots/66382bca-8bca-11ec-aade-6613bcf0e2ee/Library/Caches/com.apple.xbs/Sources/libressl/libressl-2.8/ssl/ssl_pkt.c:585:
---
Certificate chain
 0 s:/C=US/ST=Ohio/L=Cleveland/O=CWRU/CN=ec2-54-82-61-44.compute-1.amazonaws.com/emailAddress=nab2@cwru.edu
   i:/C=US/ST=OH/L=Cleveland/O=LAMPI/OU=LAMPI/CN=lampi/emailAddress=nick@barendt.com
 1 s:/C=US/ST=OH/L=Cleveland/O=LAMPI/OU=LAMPI/CN=lampi/emailAddress=nick@barendt.com
   i:/C=US/ST=OH/L=Cleveland/O=LAMPI/OU=LAMPI/CN=lampi/emailAddress=nick@barendt.com
---
Server certificate
-----BEGIN CERTIFICATE-----
MIID6jCCAtKgAwIBAgIJAMzrBdGcBJjYMA0GCSqGSIb3DQEBCwUAMH8xCzAJBgNV
BAYTAlVTMQswCQYDVQQIDAJPSDESMBAGA1UEBwwJQ2xldmVsYW5kMQ4wDAYDVQQK
DAVMQU1QSTEOMAwGA1UECwwFTEFNUEkxDjAMBgNVBAMMBWxhbXBpMR8wHQYJKoZI
hvcNAQkBFhBuaWNrQGJhcmVuZHQuY29tMB4XDTIyMDQwOTE4MjUyMFoXDTIzMDQw
OTE4MjUyMFowgY8xCzAJBgNVBAYTAlVTMQ0wCwYDVQQIDARPaGlvMRIwEAYDVQQH
DAlDbGV2ZWxhbmQxDTALBgNVBAoMBENXUlUxMDAuBgNVBAMMJ2VjMi01NC04Mi02
MS00NC5jb21wdXRlLTEuYW1hem9uYXdzLmNvbTEcMBoGCSqGSIb3DQEJARYNbmFi
MkBjd3J1LmVkdTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAK/4xrac
d94P8WWX4ho77sVzJoVUtZony1Z2Gmrx165G7D4hfkvRyFiyrJ0A3AyYyUlT4xb6
ROpwXDFCBgwet9yrcr5oFRNeR1NVbG74wdNnPNSolb3JgZbivG98UFvezYQkQrsO
49enYsM0IN9dNr8MzlDbw//cU9r/Wd7octyckEII021LUryvvTvo/2l0zaCjHqyJ
VHKGiT7ICYpZ02n6bUJbTB4WnjvV0WDTOqQfl7LlRcthBxVyU8NIvZNcWTDiXbSG
SpxwTs1KF6TIlx9Q/9OhUaKQame/je+0z2Wc7Yk36ZDBYNAN27S/ylpnQOSiF6MC
08uiDjTiYJDqdt8CAwEAAaNYMFYwCwYDVR0PBAQDAgTwMBMGA1UdJQQMMAoGCCsG
AQUFBwMBMDIGA1UdEQQrMCmCJ2VjMi01NC04Mi02MS00NC5jb21wdXRlLTEuYW1h
em9uYXdzLmNvbTANBgkqhkiG9w0BAQsFAAOCAQEAqJmvW9Ogy92QCDYMcq1jqGl9
gWjIS9KeEjlBRoxUU1jE7k/NonhQlX4UMnpvJPd8koc8ZEtjedGRN90C2rbBA+x4
3Ajvk0SSPDSloa2Cj83jKoJ9RyKg8ZXW3LBdxN9lNOIk1jeKzS5Yr/xXzyTJy1P7
AQYdH8gsc0stw+Oa1brnUI0C8zaS+Pj+q06PsDRIKeRdQ2nKd/rs3GefFFeRnw5f
dTHzXI03vG5VksrGOVVohf1GaY8MpMcc3kWfoE9HxScL8fr2Dnu27i+FPS630Osb
Px+e/JZEXz0FCAuxnAMDC/Ybt2xmbwpgCew6YIObltekxSOKvnrpOtuQtNB33A==
-----END CERTIFICATE-----
subject=/C=US/ST=Ohio/L=Cleveland/O=CWRU/CN=ec2-54-82-61-44.compute-1.amazonaws.com/emailAddress=nab2@cwru.edu
issuer=/C=US/ST=OH/L=Cleveland/O=LAMPI/OU=LAMPI/CN=lampi/emailAddress=nick@barendt.com
---
No client certificate CA names sent
Server Temp Key: ECDH, X25519, 253 bits
---
SSL handshake has read 2452 bytes and written 105 bytes
---
New, TLSv1/SSLv3, Cipher is ECDHE-RSA-AES256-GCM-SHA384
Server public key is 2048 bit
Secure Renegotiation IS supported
Compression: NONE
Expansion: NONE
No ALPN negotiated
SSL-Session:
    Protocol  : TLSv1.2
    Cipher    : ECDHE-RSA-AES256-GCM-SHA384
    Session-ID:
    Session-ID-ctx:
    Master-Key: 17DCD9C1520C3A75CCA766672064B07D5C0D56BA722A96A02B3C766A0BA68E5C0D6AB43D0255C5AF8CE9CF1B60857041
    Start Time: 1649603796
    Timeout   : 7200 (sec)
    Verify return code: 0 (ok)
---
```


Next up:  [13.3 Configuring NGINX for SSL/TLS](../13.3_Configuring_NGINX_for_SSL_TLS/README.md)

&copy; 2015-2025 LeanDog, Inc. and Nick Barendt
