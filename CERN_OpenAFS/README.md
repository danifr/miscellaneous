```
**********************************************************************************************************
  BUGS, COMMENTS, SUGGESTIONS, PLEASE OPEN AN ISSUE --> https://github.com/danifr/miscellaneous/issues
**********************************************************************************************************
```
```
RECOMMENDED: script to automate all this process: https://github.com/danifr/miscellaneous/blob/devel/CERN_OpenAFS/openafs_update.sh
```

**********************************************************************************************************

# Install and configure CERN OpenAFS on Fedora 20/21/22 Centos 7/7.1 and RHEL

## Prerequisites

Please notice that to avoid any kind of issue, you should execute the following commands as root.

- `su -`

### Installing Dependencies

- `yum install rpm-build bison flex kernel-devel kernel-devel-x86_64 krb5-devel ncurses-devel pam-devel perl-ExtUtils-Embed perl-devel`

- `yum groupinstall 'Development Tools'`

## Installing & configuring Kerberos + OpenAFS

### Kerberos Client

#### Installation

- `yum install krb5-workstation`

#### Configuration

- `wget http://linux.web.cern.ch/linux/docs/krb5.conf -O /etc/krb5.conf`

### OpenAFS Client

#### Installation

Go to the [OpenAfs official website](https://www.openafs.org/release/latest.html) and download the latest 'src.rpm' package.

- `wget https://www.openafs.org/dl/openafs/1.6.11.1/openafs-1.6.11.1-1.src.rpm`

Once downloaded:

- `rpmbuild --rebuild  openafs-1.6.11.1-1.src.rpm`

Depending on your hardware this step might take a long time. Sit back and relax :)

...

At this point we will basically need to install ALL the generated packages except `openafs-kpasswd` (because of conflicts issues with krb5-workstation) and `openafs-server` (not needed):

- `cd ~/rpmbuild/RPMS/x86_64/`

- `yum install dkms-openafs-1.6.11.1-1.fc22.x86_64.rpm kmod-openafs-1.6.11.1-1.4.0.4_301.fc22.x86_64.rpm openafs-1.6.11.1-1.fc22.x86_64.rpm openafs-authlibs-1.6.11.1-1.fc22.x86_64.rpm openafs-authlibs-devel-1.6.11.1-1.fc22.x86_64.rpm openafs-client-1.6.11.1-1.fc22.x86_64.rpm openafs-compat-1.6.11.1-1.fc22.x86_64.rpm openafs-debuginfo-1.6.11.1-1.fc22.x86_64.rpm openafs-devel-1.6.11.1-1.fc22.x86_64.rpm openafs-docs-1.6.11.1-1.fc22.x86_64.rpm openafs-kernel-source-1.6.11.1-1.fc22.x86_64.rpm openafs-krb5-1.6.11.1-1.fc22.x86_64.rpm`

#### Configuration

Edit '/usr/vice/etc/ThisCell'...

- `echo "cern.ch" > /usr/vice/etc/ThisCell`

... and add the following lines to '/etc/krb5.conf':

```
[realms]
  CERN.CH = {
    default_domain = cern.ch
    kpasswd_server = afskrb5m.cern.ch
    admin_server = afskrb5m.cern.ch
    kdc = afsdb1.cern.ch        # ADD THIS LINE
    kdc = afsdb2.cern.ch        # ADD THIS LINE
    kdc = afsdb3.cern.ch        # ADD THIS LINE
  }

[domain_realm]
  cern.ch = CERN.CH             # ADD THIS LINE
  .cern.ch = CERN.CH
```

Finally, start and enable the service.

- `systemctl start openafs-client.service`

- `systemctl enable openafs-client.service`

## Usage

To start using it, you will need valid kerberos ticket:

- `kinit <username>@CERN.CH`

And also mount the afs share on the our system:

- `aklog`

After doing it, you will be able to access your personal share from:

`/afs/cern.ch/user/<first_letter_username>/<username>`
