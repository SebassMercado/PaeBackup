from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from modelos.usuarios.models import Usuario, PasswordResetToken

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create(
            documento=123456,
            nombres='Test',
            apellidos='User',
            telefono=3000000000,
            direccion='Calle 1',
            correo='test@example.com',
            rol='EV',
            password='plainpass',  # Será hasheada en save()
            estado='A'
        )

    def test_password_reset_request_creates_token_and_sends_email(self):
        url = reverse('usuarios:password_reset_request')
        resp = self.client.post(url, {'correoDocumento': self.user.correo})
        self.assertEqual(resp.status_code, 200)
        # Token creado
        token_obj = PasswordResetToken.objects.filter(usuario=self.user).first()
        self.assertIsNotNone(token_obj, 'Debe crearse un token de recuperación')
        self.assertEqual(len(token_obj.codigo), 6)
        # Email enviado
        self.assertEqual(len(mail.outbox), 1, 'Se debe enviar un correo de recuperación')
        self.assertIn(token_obj.codigo, mail.outbox[0].body)

    def test_password_reset_confirm_changes_password(self):
        # Crear token manual
        token_obj = PasswordResetToken.objects.create(usuario=self.user, token='manualtoken', codigo='999999')
        url = reverse('usuarios:password_reset_confirm', args=[token_obj.token])
        resp = self.client.post(url, {
            'password': 'nuevaSegura123',
            'password2': 'nuevaSegura123'
        })
        self.assertEqual(resp.status_code, 302)  # redirect to login
        # Refrescar usuario
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nuevaSegura123'))
        token_obj.refresh_from_db()
        self.assertTrue(token_obj.usado)

    def test_password_reset_verify_with_code(self):
        # Generar token reciente
        token_obj = PasswordResetToken.objects.create(usuario=self.user, token='tokentest', codigo='123456')
        url = reverse('usuarios:password_reset_verify')
        resp = self.client.post(url, {
            'correoDocumento': self.user.correo,
            'codigo': '123456',
            'password': 'otraClave321',
            'password2': 'otraClave321'
        })
        self.assertEqual(resp.status_code, 302)  # redirect login
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('otraClave321'))
        token_obj.refresh_from_db()
        self.assertTrue(token_obj.usado)

    def test_password_reset_verify_invalid_code(self):
        PasswordResetToken.objects.create(usuario=self.user, token='tokentest', codigo='123456')
        url = reverse('usuarios:password_reset_verify')
        resp = self.client.post(url, {
            'correoDocumento': self.user.correo,
            'codigo': '000000',
            'password': 'xClave123',
            'password2': 'xClave123'
        })
        # No redirect, muestra error
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(PasswordResetToken.objects.get(codigo='123456').usado)
