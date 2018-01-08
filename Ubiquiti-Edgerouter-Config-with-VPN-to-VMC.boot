/* Most of my current Ubiquiti Edgerouter Config */
/* IP Addresses (Internally as well as public) have been changed here to not reflect my personal IPs */
firewall {
    all-ping enable
    broadcast-ping disable
    ipv6-name WANv6_IN {
        default-action drop
        description "WAN inbound traffic forwarded to LAN"
        rule 10 {
            action accept
            description "Allow established/related"
            state {
                established enable
                related enable
            }
        }
        rule 20 {
            action drop
            description "Drop invalid state"
            state {
                invalid enable
            }
        }
        rule 30 {
            action accept
            description "Allow ICMPv6"
            log disable
            protocol icmpv6
        }
    }
    ipv6-name WANv6_LOCAL {
        default-action drop
        description "WAN inbound traffic to the router"
        rule 10 {
            action accept
            description "Allow established/related"
            state {
                established enable
                related enable
            }
        }
        rule 20 {
            action drop
            description "Drop invalid state"
            state {
                invalid enable
            }
        }
        rule 30 {
            action accept
            description "Allow ICMPv6"
            log disable
            protocol icmpv6
        }
        rule 40 {
            action accept
            description "Allow DHCPv6"
            destination {
                port 546
            }
            protocol udp
            source {
                port 547
            }
        }
    }
    ipv6-name WANv6_OUT {
        default-action accept
        description "WAN outbound traffic"
        rule 10 {
            action accept
            description "Allow established/related"
            state {
                established enable
                related enable
            }
        }
        rule 20 {
            action reject
            description "Reject invalid state"
            state {
                invalid enable
            }
        }
    }
    ipv6-receive-redirects disable
    ipv6-src-route disable
    ip-src-route disable
    log-martians enable
    name LAN_IN {
        default-action accept
        description "LAN to Internal"
        rule 10 {
            action drop
            description "Drop invalid state"
            state {
                invalid enable
            }
        }
    }
    name WAN_IN {
        default-action drop
        description "WAN to internal"
        rule 10 {
            action accept
            description "Allow established/related"
            log disable
            state {
                established enable
                invalid disable
                new disable
                related enable
            }
        }
        rule 30 {
            action accept
            description "Allow ICMP"
            log disable
            protocol icmp
            state {
                established enable
                related enable
            }
        }
        rule 40 {
            action accept
            description "Allow IGMP"
            log disable
            protocol igmp
        }
        rule 50 {
            action drop
            description "Drop invalid state"
            protocol all
            state {
                established disable
                invalid enable
                new disable
                related disable
            }
        }
    }
    name WAN_LOCAL {
        default-action drop
        description "WAN to router"
        rule 10 {
            action accept
            description "Allow established/related"
            log disable
            state {
                established enable
                related enable
            }
        }
        rule 20 {
            action accept
            description "Management VPN"
            destination {
                address 172.1.0.1 /* Address of your Router (internally) */
            }
            log disable
            protocol all
            source {
                address 50.16.95.152 /* MGMT Gateway IP Found in VMC Console */
            }
        }
        rule 30 {
            action accept
            description VPN
            destination {
                address 172.1.0.1 /* Address of your Router (internally) */
            }
            log disable
            protocol all
            source {
                address 34.234.39.55 /* Compute Gateway IP Found in VMC Console */
            }
        }

        rule 60 {
            action accept
            description "Allow ICMP"
            log disable
            protocol icmp
        }
        rule 70 {
            action drop
            description "Drop invalid state"
            protocol all
            state {
                established disable
                invalid enable
                new disable
                related disable
            }
        }
    }
    name WAN_OUT {
        default-action accept
        description "Internal to WAN"
        rule 10 {
            action accept
            description "Allow established/related"
            log disable
            state {
                established enable
                related enable
            }
        }
        rule 20 {
            action reject
            description "Reject invalid state"
            state {
                invalid enable
            }
        }
    }
    options {
        mss-clamp {
            interface-type all
            mss 1460
        }
    }
    receive-redirects disable
    send-redirects enable
    source-validation disable
    syn-cookies enable
}
interfaces {
    ethernet eth0 {
        description "Google Fiber Jack"
        duplex auto
        speed auto
        vif 2 {
            address dhcp
            description "Google Fiber WAN"
            dhcpv6-pd {
                pd 0 {
                    interface switch0 {
                        host-address ::1
                        prefix-id :0
                        service slaac
                    }
                    interface switch0.102 {
                        host-address ::1
                        prefix-id :1
                        service slaac
                    }
                    prefix-length /56
                }
                rapid-commit enable
            }
            egress-qos 0:3
            firewall {
                in {
                    ipv6-name WANv6_IN
                    name WAN_IN
                }
                local {
                    ipv6-name WANv6_LOCAL
                    name WAN_LOCAL
                }
                out {
                    ipv6-name WANv6_OUT
                    name WAN_OUT
                }
            }
        }
    }
    ethernet eth1 {
        description LAN
        duplex auto
        speed auto
    }
    ethernet eth2 {
        description LAN
        duplex auto
        speed auto
    }
    ethernet eth3 {
        description LAN
        duplex auto
        speed auto
    }
    ethernet eth4 {
        description Guest
        duplex auto
        speed auto
    }
    loopback lo {
    }
    switch switch0 {
        address 172.1.0.1/16
        description "LAN Switch"
        firewall {
            in {
                name LAN_IN
            }
        }
        mtu 1500
        switch-port {
            interface eth1 {
            }
            interface eth2 {
            }
            interface eth3 {
            }
            vlan-aware disable
        }
        vif 102 {
            address 172.16.0.1/24
            description "Guest Network VLAN"
            mtu 1500
        }
    }
}
port-forward {
    auto-firewall enable
    hairpin-nat enable
    lan-interface switch0

    rule 6 {
        description IPSEC
        forward-to {
            address 172.1.0.1
            port 500
        }
        original-port 500
        protocol udp
    }
    rule 7 {
        description IPSEC
        forward-to {
            address 172.1.0.1
            port 4500
        }
        original-port 4500
        protocol udp
    }
    rule 8 {
        description IPSEC
        forward-to {
            address 172.1.0.1
            port 50
        }
        original-port 50
        protocol tcp_udp
    }
    rule 9 {
        description IPSEC
        forward-to {
            address 172.1.0.1
            port 51
        }
        original-port 51
        protocol tcp_udp
    }
    wan-interface eth0.2
}
service {
    dhcp-server {
        disabled false
        hostfile-update enable
        shared-network-name Guest {
            authoritative disable
            subnet 172.16.0.0/24 {
                default-router 172.16.0.1
                dns-server 8.8.8.8
                dns-server 8.8.4.4
                domain-name guest.example.com
                lease 86400
                start 172.16.0.10 {
                    stop 172.16.0.254
                }
            }
        }
        shared-network-name LAN {
            authoritative disable
            subnet 172.1.0.0/16 {
                default-router 172.1.0.1
                dns-server 172.1.0.1
                dns-server 8.8.8.8
                dns-server 8.8.4.4
                domain-name example.com
                lease 86400
                start 172.1.99.1 {
                    stop 172.1.99.254
                }
            }
        }
        use-dnsmasq disable
    }
    dns {
        forwarding {
            cache-size 500
            listen-on switch0
            name-server 2001:4860:4860::8888
            name-server 2001:4860:4860::8844
            name-server 8.8.8.8
            name-server 8.8.4.4
        }
    }
    gui {
        http-port 80
        https-port 443
        older-ciphers enable
    }
    nat {
        rule 5000 {
            description "Masquerade for WAN"
            outbound-interface eth0.2
            protocol all
            type masquerade
        }
    }
    ssh {
        port 22
        protocol-version v2
    }
    upnp2 {
        listen-on switch0
        nat-pmp disable
        secure-mode enable
        wan eth0.2
    }
}
/* Copy and Paste the System section from your current UBNT Edrouter to this one */
system {
    host-name UBNT-gateway
    login {
        user admin1 {
            authentication {
                encrypted-password ENCRYPTEDPASSWORDHERE
                plaintext-password ""
            }
            level admin
        }
        user adduserhere {
            authentication {
                encrypted-password ENCRYPTEDPASSWORDHERE
                plaintext-password ""
            }
            level admin
        }
    }
    name-server 2001:4860:4860::8888
    name-server 2001:4860:4860::8844
    name-server 8.8.8.8
    name-server 8.8.4.4
    ntp {
        server 0.ubnt.pool.ntp.org {
        }
        server 1.ubnt.pool.ntp.org {
        }
        server 2.ubnt.pool.ntp.org {
        }
        server 3.ubnt.pool.ntp.org {
        }
    }
    offload {
        hwnat enable
        ipsec enable
    }
    package {
        repository wheezy {
            components "main contrib non-free"
            distribution wheezy
            password ""
            url http://http.us.debian.org/debian
            username ""
        }
    }
    syslog {
        global {
            facility all {
                level notice
            }
            facility protocols {
                level debug
            }
        }
    }
    time-zone America/Denver
    traffic-analysis {
        dpi disable
        export enable
    }
}

/* VPN SETTINGS FOR VMC TO HOMELAB */
vpn {
    ipsec {
        auto-firewall-nat-exclude enable
        esp-group FOO0 {
            compression disable
            lifetime 3600
            mode tunnel
            pfs enable
            proposal 1 {
                encryption aes256
                hash sha1
            }
        }
        esp-group FOO1 {
            compression disable
            lifetime 3600
            mode tunnel
            pfs enable
            proposal 1 {
                encryption aes256
                hash sha1
            }
        }
        ike-group FOO0 {
            ikev2-reauth no
            key-exchange ikev1
            lifetime 28800
            proposal 1 {
                dh-group 14
                encryption aes256
                hash sha1
            }
        }
        ike-group FOO1 {
            ikev2-reauth no
            key-exchange ikev1
            lifetime 28800
            proposal 1 {
                dh-group 14
                encryption aes256
                hash sha1
            }
        }
        site-to-site {
            peer 34.234.39.55 /* The Public IP address of the Compute Gateway in VMC Console */ {
                authentication {
                    mode pre-shared-secret
                    pre-shared-secret thisisourinternet
                }
                connection-type initiate
                description "COMPUTE VPN"
                ike-group FOO0
                ikev2-reauth inherit
                local-address 45.56.32.50 /* Your Public IP */
                tunnel 1 {
                    allow-nat-networks disable
                    allow-public-networks disable
                    esp-group FOO0
                    local {
                        prefix 172.1.0.0/16 /* Your Homelab Network segment */
                    }
                    remote {
                        prefix 192.168.0.1/24 /* VMC Workload Subnet that will be connected */
                    }
                }
            }
            peer 50.16.95.152  /* The Public IP address of the Management Gateway in VMC Console */ {
                authentication {
                    mode pre-shared-secret
                    pre-shared-secret thisisourinternet
                }
                connection-type initiate
                description "Management VPN"
                ike-group FOO1
                ikev2-reauth inherit
                local-address 45.56.32.50 /* Your Public IP */
                tunnel 1 {
                    allow-nat-networks disable
                    allow-public-networks disable
                    esp-group FOO1
                    local {
                        prefix 172.1.0.0/16 /* Your Homelab Network segment */
                    }
                    remote {
                        prefix 10.0.0.0/16 /* VMC Management Subnet that will be connected */
                    }
                }
            }
        }
    }
}


/* Warning: Do not remove the following line. */
/* === vyatta-config-version: "config-management@1:conntrack@1:cron@1:dhcp-relay@1:dhcp-server@4:firewall@5:ipsec@5:nat@3:qos@1:quagga@2:system@4:ubnt-pptp@1:ubnt-util@1:vrrp@1:webgui@1:webproxy@1:zone-policy@1" === */
/* Release version: v1.9.1.4939092.161214.0702 */
