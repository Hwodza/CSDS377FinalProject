# Serving Django from NGINX

Next we need to secure our web client, and switch from HTTP to HTTPS.

## Troubleshooting

If you have trouble with the configuration, you can observe the NGINX logs:

```bash
sudo tail /var/log/nginx/error.log
```

or

```bash
sudo tail -f /var/log/nginx/error.log
```

to see updates to the log as they are appended to the file in real time.

Most errors at this point are likely to be configuration-based, so double-check those **.conf** files!

## Configure TLS

First we are going to open up a port for testing. Navigate to **console.aws.amazon.com**, click on **EC2**, click on **Security Groups**, and add an inbound rule to allow access to TCP port **443**, the standard port for HTTPS. While you're in there, remove access to port 8080 and any other unneeded ports. At this point, we're done with unencrypted HTTP (a real prooduction site would probably allow limited HTTP connections to port 80, with an automatic redirect to HTTPS on port 443).

Navigate to your NGINX sites-available directory and edit **lampisite.conf**. Change the listen port to 443 and add the needed settings for ssl:

```
# configuration of the server
server {

    # the port your site will be served on
    listen 443 ssl;
    ssl_certificate /home/ubuntu/ssl_keys/lampi_server.crt;
    ssl_certificate_key /home/ubuntu/ssl_keys/lampi_server.key;
    ssl_protocols TLSv1.2;

    # the domain name it will serve for
    server_name ec2-52-20-29-213.compute-1.amazonaws.com; # CHANGE to match your machine's FQDN
    charset     utf-8;
```

Install the Certificates and Private Keys in the directories specified.

**NOTE:** just as we would never deploy production code in a user home directory, we would never store cryptographic keys, certificates, etc. there.  Doing so simplifies the class work, though.

Restart uWSGI again and restart NGINX:

```bash
cloud$ sudo systemctl restart lampi_uwsgi
cloud$ sudo service nginx restart
```

Now on your host machine navigate to `https://{server_fqdn}` (note the **https**) to see the default page. You should be notified in some way that the page isn't trusted, or the certificate isn't verified, or something along these lines. Bypass this warning if possible to see your Django page.

We got those warnings because we are acting as our own Certificate Authority, the certs we sign are not trusted by default. There are many CAs that are trusted by default on modern systems (of which VeriSign is an example). For basic needs like serving web pages, most of the time you'll find yourself buying a cert from one of those CAs. For specialized needs such as the communication between devices such as our LAMPIs and the server, acting as a Certificate Authority provides some additional control that may be desired or needed.

## Make our CA Root Certificate Trusted

Let's configure our browsers to trust our CA on our computer so we can connect to the website without any errors or warnings.
 
You'll need to install our CA Root Certificate as a trusted root:

- [Windows](http://www.thewindowsclub.com/manage-trusted-root-certificates-windows)
	- Note:, you will need convert your certificate in PEM format to another format, PKCS#12.  Uou can use the [OpenSSL PKCS#12](https://www.openssl.org/docs/manmaster/man1/openssl-pkcs12.html) tool, something like `openssl pkcs12 -export -in lampi_ca.crt -inkey lampi_ca.key -out lampi_ca.pfx` to convert it.
	- if you have Windows Home Edition you will need to run the Management Console (`mmc.exe`)
		- add the Certificates snap-in, ; please see, for example, [this](https://www.itechtics.com/update-root-certificates/)
		- Import your certificate in PKCS#12 format see for example [this](https://www.itechtics.com/update-root-certificates/#import-root-certificates)
- [OSX Add certficates to Keychain](https://support.apple.com/guide/keychain-access/add-certificates-to-a-keychain-kyca2431/mac) and [OSX Change Trust Settings](https://support.apple.com/guide/keychain-access/change-the-trust-settings-of-a-certificate-kyca11871/mac).  This [Stackoverflow link](https://apple.stackexchange.com/questions/123988/how-to-add-a-crt-certificate-to-iphones-keychain) is also helpful for iOS.
- **FireFox** - there are issues using Firefox with self-signed certificates, particularly for the WSS (Secure Websockets) connection for MQTT.  Suggest using an alternate browser for this assignment.
- **Ubuntu** - It's [possible](https://ubuntu.com/server/docs/install-a-root-ca-certificate-in-the-trust-store) to install a certificate globally, but both Firefox and Chromium ignore these. [StackExchange](https://askubuntu.com/questions/244582/add-certificate-authorities-system-wide-on-firefox) has a possibility for Firefox, but it's easiest to to use Chromium, which has a browser GUI for adding certs: `chrome://settings/certificates` > Authorities > Import.


Navigate back to `https://{server_fqdn}`. 

It should load with no certificate warnings / trust issues. 

**NOTE: It is important to have this working, as websockets will not work at all unless the certificate is trusted by your browser.**

Next up: go to [13.4 Assignment](../13.4_Assignment/README.md)

&copy; 2015-2025 LeanDog, Inc. and Nick Barendt
