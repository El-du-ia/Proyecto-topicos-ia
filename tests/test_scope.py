import pytest

from dui.security import Scope, ScopeError


def resolver(mapping):
    def resolve(host):
        if host not in mapping:
            raise OSError("no resuelve")
        return mapping[host]

    return resolve


@pytest.mark.parametrize(
    "target", ["192.168.1.10", "192.168.1.0/24", "10.0.0.5", "127.0.0.1", "::1", "172.16.4.4"]
)
def test_private_networks_allowed_by_default(target):
    assert Scope().check(target)[0]


@pytest.mark.parametrize("target", ["8.8.8.8", "10.0.0.0/7", "0.0.0.0/0", "2001:4860::8888"])
def test_public_or_too_wide_targets_rejected_by_default(target):
    allowed, message = Scope().check(target)
    assert not allowed and "FUERA del alcance" in message


@pytest.mark.parametrize("target", ["-iL", "-oN out.txt", "1.2.3.4; rm -rf /", "a b", "", "$(id)"])
def test_option_or_shell_injection_rejected(target):
    allowed, _ = Scope().check(target)
    assert not allowed
    with pytest.raises(ScopeError):
        Scope().ensure_allowed(target)


def test_custom_networks_and_subnets():
    scope = Scope(["203.0.113.0/24"])
    assert scope.check("203.0.113.7")[0]
    assert scope.check("203.0.113.0/25")[0]
    assert not scope.check("203.0.0.0/16")[0]


def test_domains_cover_subdomains_without_resolving():
    scope = Scope(["example.com"], resolver=resolver({}))
    assert scope.check("example.com")[0]
    assert scope.check("www.example.com")[0]
    assert not scope.check("example.com.evil.net")[0]


def test_hostname_allowed_only_if_all_addresses_in_scope():
    scope = Scope(resolver=resolver({"nas.local": ["192.168.1.5"], "mixed.test": ["192.168.1.5", "8.8.8.8"]}))
    assert scope.check("nas.local")[0]
    assert not scope.check("mixed.test")[0]
    assert "No se pudo resolver" in scope.check("nope.test")[1]


def test_add_validates_and_describes():
    scope = Scope()
    scope.add("*.lab.test")
    scope.add("198.51.100.1")
    assert scope.domains == ["lab.test"]
    assert "198.51.100.1/32" in scope.describe()
    with pytest.raises(ScopeError):
        scope.add("-bad")
