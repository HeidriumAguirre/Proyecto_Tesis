"""
Tests para core.auth.
Validan verificacion de contrasena bcrypt sin necesidad de MySQL.
"""
import bcrypt

from core.auth import _verificar_password


def test_verificar_password_correcta():
    plain = "Demo2026!"
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=4))
    assert _verificar_password(plain, hashed.decode("utf-8")) is True


def test_verificar_password_incorrecta():
    hashed = bcrypt.hashpw(b"correcta", bcrypt.gensalt(rounds=4))
    assert _verificar_password("incorrecta", hashed.decode("utf-8")) is False


def test_verificar_password_hash_invalido():
    assert _verificar_password("cualquiera", "no-es-un-hash-bcrypt") is False


def test_verificar_password_vacia():
    assert _verificar_password("", "x") is False
