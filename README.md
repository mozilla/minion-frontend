This project contains the code for the Minion Frontend.  It provides an simple HTML to manage users and groups,
control sites, and create and start scans.

Setting up a Development Environment
------------------------------------

Note that Mozilla maintains [Vagrant and Docker configurations](https://github.com/mozilla/minion-vm/) for Minion.
It's the best and easiest way to get started with development!

The following instructions for manual installation assume a recent version of Ubuntu; we currently test with Ubuntu
14.04 LTS (Trusty Tahr). Although Minion can be installed anywhere on your system, we recommend·
`/opt/minion/minion-frontend` for the frontend, and `/opt/minion/minion-env` for your virtualenv.

First, install the essentials:

```
# apt-get update
# apt-get install -y build-essential git libldap2-dev libsasl2-dev \
    libssl-dev python python-dev python-virtualenv supervisor
```

Then, create and source your virtual environment.  This will help keep Minion isolated from the rest of your system. We
also need to upgrade setuptools from the version included with Ubuntu by default:

```
# mkdir -p /etc/minion /opt/minion
# cd /opt/minion
# virtualenv minion-env
# source minion-env/bin/activate

(minion-env)# easy_install --upgrade setuptools    # required for Mock
```

Next, setup your system with the following directories and the `minion` user account. We'll also create some convenience
shell commands, to make working with Minion easier when running as the `minion` user:

```
# useradd -m minion
# install -m 700 -o minion -g minion -d /run/minion -d /var/lib/minion -d /var/log/minion -d ~minion/.python-eggs

# echo -e "\n# Automatically source minion-frontend virtualenv" >> ~minion.profile
# echo -e "source /opt/minion/minion-env/bin/activate" >> ~minion/.profile

# echo -e "\n# Minion convenience commands" >> ~minion/.bashrc
# echo -e "alias miniond=\"supervisord -c /opt/minion/minion-frontend/etc/supervisord.conf\"" >> ~minion/.bashrc
# echo -e "alias minionctl=\"supervisorctl -c /opt/minion/minion-frontend/etc/supervisord.conf\"" >> ~minion/.bashrc
```

Now we can checkout Minion and install it:

```
# cd /opt/minion
# git clone https://github.com/mozilla/minion-frontend.git
# source minion-env/bin/activate
(minion-env)# python setup.py develop
```

To make sure that Minion starts when the system reboots, we need to install the Minion init script. We can also disable
the global `supervisord` installed with `apt-get install` above, if it wasn't being used before:

```
# cp /opt/minion/minion-frontend/scripts/minion-init /etc/init.d/minion
# chown root:root /etc/init.d/minion
# chmod 755 /etc/init.d/minion
# update-rc.d minion defaults 40
# update-rc.d -f supervisor remove
```

And that's it! Provided that everything installed successfully, we can start everything up:

```
# service minion start
```

From this point on, you should be able to control the Minion processes either as root or as the newly-created minion user.
Let's `su - minion`, and see if everything is running properly:

```
(minion-env)minion@minion-frontend:~$ service minion status
minion-frontend                  RUNNING    pid 1506, uptime 1 day, 1:25:41
```

Success! You can also use `minionctl` (an alias to `supervisorctl`, using the Minion `supervisord.conf` configuration)
to stop and start individual services, or check on status:

```
(minion-env)minion@minion-frontend:~$ minionctl stop minion-frontend
minion-frontend: stopped
(minion-env)minion@minion-frontend:~$ minionctl status minion-frontend
minion-frontend                  STOPPED    Sep 09 07:15 PM
(minion-env)minion@minion-frontend:~$ minionctl start minion-frontend
minion-frontend: started
(minion-env)minion@minion-frontend:~$ minionctl status minion-frontend
minion-frontend                  RUNNING    pid 8713, uptime 0:00:05
```

Configuring your Minion environment
-----------------------------------

By default, Minion will use the configuration file `frontend.json` to determine the authentication method as well as the
location of the [Minion backend](https://github.com/mozilla/minion-backend). If you would like to change this file at all,
copy it into `/etc/minion`, make your changes, and restart Minion.

Minion currently supports both Persona and LDAP authentication, with Persona being the default authentication method. To
switch to LDAP authentication, change `type` in `login` from `persona` to `ldap`, and change the `ldap` configuration
section to point to the correct LDAP server and base DN.
