from fabric import Connection

f= open("node_ip","r")
node_ip  = f.read()
f.close

f= open("key_pair","r")
key_pair  = f.read()
f.close

c = Connection(
        host=node_ip,
        user="ubuntu",
        connect_kwargs={
            "key_filename": key_pair + ".pem",
        },
    )
try:
    print('Please access the online bookstore at this IP address: %s' %node_ip)
    print('To stop running the online bookstore, press ctrl+c')
    input('Press enter to launch the online bookstore!')
    print('Launching online bookstore...')
    # c.sudo('kill -9 $(sudo lsof -t -i:3000)')
    c.sudo('iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3000')
    c.run('cd DoubleNoQL/myapp && npm start')
except KeyboardInterrupt:
    print('Bringing down Online Bookstore!')
    c.sudo('kill -9 $(sudo lsof -t -i:3000)')
