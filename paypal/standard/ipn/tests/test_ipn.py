# -*- coding: utf-8 -*-

import urllib

from django.conf import settings
from django.test import TestCase

from paypal.standard.models import ST_PP_CANCELLED, ST_PP_REFUNDED, ST_PP_COMPLETED

from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.ipn.signals import (payment_was_successful,
    payment_was_flagged, recurring_skipped, recurring_failed,
    recurring_create, recurring_payment, recurring_cancel,
    recurring_refunded, payment_refunded, subscription_failed, subscription_eot,
    subscription_signup, subscription_cancel)


# Parameters are all bytestrings, so we can construct a bytestring
# request the same way that Paypal does.

IPN_POST_PARAMS = {
    "protection_eligibility": "Ineligible",
    "last_name": "User",
    "txn_id": "51403485VH153354B",
    "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
    "payment_status": ST_PP_COMPLETED,
    "payment_gross": "10.00",
    "tax": "0.00",
    "residence_country": "US",
    "invoice": "0004",
    "payer_status": "verified",
    "txn_type": "express_checkout",
    "handling_amount": "0.00",
    "payment_date": "23:04:06 Feb 02, 2009 PST",
    "first_name": "J\xF6rg",
    "item_name": "",
    "charset": "windows-1252",
    "custom": "website_id=13&user_id=21",
    "notify_version": "2.6",
    "transaction_subject": "",
    "test_ipn": "1",
    "item_number": "",
    "receiver_id": "258DLEHY2BDK6",
    "payer_id": "BN5JZ2V7MLEV4",
    "verify_sign": "An5ns1Kso7MWUdW4ErQKJJJ4qi4-AqdZy6dD.sGO3sDhTf1wAbuO2IZ7",
    "payment_fee": "0.59",
    "mc_fee": "0.59",
    "mc_currency": "USD",
    "shipping": "0.00",
    "payer_email": "bishan_1233269544_per@gmail.com",
    "payment_type": "instant",
    "mc_gross": "10.00",
    "quantity": "1",
}


IPN_SUBSCR_FAILED_PARAMS = {
    "business": "abc",
    "charset": "UTF-8",
    "custom": "1,2,3,4",
    "first_name": "J\xF6rg",
    "ipn_track_id": "a5u81abcd1234",
    "item_name": "Item Name",
    "item_number": "itemname",
    "last_name": "Smith",
    "mc_currency": "JPY",
    "mc_gross": "999",
    "notify_version": "3.7",
    "payer_business_name": "Biz Name",
    "payer_email": "payer@example.com",
    "payer_id": "YXNBI1GQZPV6M",
    "payer_status": "verified",
    "payment_gross": "",
    "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
    "residence_country": "JP",
    "retry_at": "02:00:00 Nov 24, 2012 PST",
    "subscr_id": "I-1EM1WEKXTL1G",
    "txn_type": "subscr_failed",
    "verify_sign": "",
}

IPN_SUBSCR_SIGNUP_PARAMS = {
    "business": "abc",
    "charset": "UTF-8",
    "custom": "1,2,3,4",
    "first_name": "J\xF6rg",
    "ipn_track_id": "a5u81abcd1234",
    "item_name": "monthly widgets",
    "item_number": "1234",
    "last_name": "Smith",
    "mc_amount3": "999",
    "mc_currency": "JPY",
    "notify_version": "3.7",
    "payer_email": "payer@example.com",
    "payer_id": "YXNBI1GQZPV6M",
    "payer_status": "verified",
    "period3": "1+M",
    "reattempt": "1",
    "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
    "recurring": "1",
    "residence_country": "JP",
    "subscr_date": "05:11:33 Nov 16, 2012 PST",
    "subscr_id": "I-1EM1WEKXTL1G",
    "txn_type": "subscr_signup",
    "verify_sign": "",
}

IPN_SUBSCR_EOT_PARAMS = {
    "business": "business@example.com",
    "charset": "UTF-8",
    "custom": "1,2,3,4",
    "first_name": "J\xF6rg",
    "ipn_track_id": "a5u81abcd1234",
    "item_name": "monthly widgets",
    "item_number": "1234",
    "last_name": "Smith",
    "mc_currency": "JPY",
    "notify_version": "3.7",
    "payer_email": "payer@example.com",
    "payer_id": "YXNBI1GQZPV6M",
    "payer_status": "verified",
    "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
    "residence_country": "JP",
    "subscr_id": "I-1EM1WEKXTL1G",
    "txn_type": "subscr_eot",
    "verify_sign": "",
}


IPN_SUBSCR_CANCEL_PARAMS = {
    "business": "business@example.com",
    "charset": "UTF-8",
    "custom": "1,2,3,4",
    "first_name": "J\xF6rg",
    "ipn_track_id": "a5u81abcd1234",
    "item_name": "monthly widgets",
    "item_number": "1234",
    "last_name": "Smith",
    "mc_amount3": "3000",
    "mc_currency": "JPY",
    "notify_version": "3.7",
    "payer_email": "payer@example.com",
    "payer_id": "YXNBI1GQZPV6M",
    "payer_status": "verified",
    "period3": "1+M",
    "reattempt": "1",
    "receiver_email": settings.PAYPAL_RECEIVER_EMAIL,
    "recurring": "1",
    "residence_country": "JP",
    "subscr_date": "21:05:00 Sep 27, 2012 PDT",
    "subscr_id": "I-1EM1WEKXTL1G",
    "txn_type": "subscr_cancel",
    "verify_sign": "",
}

class IPNTest(TestCase):
    urls = 'paypal.standard.ipn.tests.test_urls'

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True

        # Monkey patch over PayPalIPN to make it get a VERFIED response.
        self.old_postback = PayPalIPN._postback
        PayPalIPN._postback = lambda self: "VERIFIED"

        self.payment_was_successful_receivers = payment_was_successful.receivers
        self.payment_was_flagged_receivers = payment_was_flagged.receivers
        self.payment_refunded_receivers = payment_refunded.receivers

        self.recurring_skipped_receivers = recurring_skipped.receivers
        self.recurring_failed_receivers = recurring_failed.receivers
        self.recurring_create_receivers = recurring_create.receivers
        self.recurring_payment_receivers = recurring_payment.receivers
        self.recurring_cancel_receivers = recurring_cancel.receivers
        self.recurring_refunded_receivers = recurring_refunded.receivers

        self.subscription_signup_receivers = subscription_signup.receivers
        self.subscription_failed_receivers = subscription_failed.receivers
        self.subscription_eot_receivers = subscription_eot.receivers
        self.subscription_cancel_receivers = subscription_cancel.receivers

        payment_was_successful.receivers = []
        payment_was_flagged.receivers = []
        payment_refunded.receivers = []

        recurring_skipped.receivers = []
        recurring_failed.receivers = []
        recurring_create.receivers = []
        recurring_payment.receivers = []
        recurring_cancel.receivers = []
        recurring_refunded.receivers = []

        subscription_signup.receivers = []
        subscription_failed.receivers = []
        subscription_eot.receivers = []
        subscription_cancel.receivers = []


    def tearDown(self):
        settings.DEBUG = self.old_debug
        PayPalIPN._postback = self.old_postback

        payment_was_successful.receivers =self.payment_was_successful_receivers
        payment_was_flagged.receivers = self.payment_was_flagged_receivers
        payment_refunded.receivers = self.payment_refunded_receivers

        recurring_skipped.receivers = self.recurring_skipped_receivers
        recurring_failed.receivers = self.recurring_failed_receivers
        recurring_create.receivers = self.recurring_create_receivers
        recurring_payment.receivers = self.recurring_payment_receivers
        recurring_cancel.receivers = self.recurring_cancel_receivers

        subscription_signup.receivers = self.subscription_signup_receivers
        subscription_failed.receivers = self.subscription_failed_receivers
        subscription_eot.receivers = self.subscription_eot_receivers
        subscription_cancel.receivers = self.subscription_cancel_receivers


    def paypal_post(self, params):
        """
        Does an HTTP POST the way that PayPal does, using the params given.
        """
        # We build params into a bytestring ourselves, to avoid some encoding
        # processing that is done by the test client.
        post_data = urllib.urlencode(params)
        return self.client.post("/ipn/", post_data, content_type='application/x-www-form-urlencoded')


    def assertGotSignal(self, signal, flagged, params=IPN_POST_PARAMS):
        # Check the signal was sent. These get lost if they don't reference self.
        self.got_signal = False
        self.signal_obj = None

        def handle_signal(sender, **kwargs):
            self.got_signal = True
            self.signal_obj = sender
        signal.connect(handle_signal)

        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        ipns = PayPalIPN.objects.all()
        self.assertEqual(len(ipns), 1)
        ipn_obj = ipns[0]
        self.assertEqual(ipn_obj.flag, flagged)

        self.assertTrue(self.got_signal)
        self.assertEqual(self.signal_obj, ipn_obj)
        return ipn_obj

    def test_correct_ipn(self):
        ipn_obj = self.assertGotSignal(payment_was_successful, False)
        # Check some encoding issues:
        self.assertEqual(ipn_obj.first_name, u"J\u00f6rg")

    def test_failed_ipn(self):
        PayPalIPN._postback = lambda self: "INVALID"
        self.assertGotSignal(payment_was_flagged, True)

    def assertFlagged(self, updates, flag_info):
        params = IPN_POST_PARAMS.copy()
        params.update(updates)
        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        ipn_obj = PayPalIPN.objects.all()[0]
        self.assertEqual(ipn_obj.flag, True)
        self.assertEqual(ipn_obj.flag_info, flag_info)

    def test_incorrect_receiver_email(self):
        update = {"receiver_email": "incorrect_email@someotherbusiness.com"}
        flag_info = "Invalid receiver_email. (incorrect_email@someotherbusiness.com)"
        self.assertFlagged(update, flag_info)

    def test_invalid_payment_status(self):
        update = {"payment_status": "Failed"}
        flag_info = u"Invalid payment_status. (Failed)"
        self.assertFlagged(update, flag_info)

    def test_vaid_payment_status_cancelled(self):
        update = {"payment_status": ST_PP_CANCELLED}
        params = IPN_POST_PARAMS.copy()
        params.update(update)
        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        ipn_obj = PayPalIPN.objects.all()[0]
        self.assertEqual(ipn_obj.flag, False)

    def test_duplicate_txn_id(self):
        self.paypal_post(IPN_POST_PARAMS)
        self.paypal_post(IPN_POST_PARAMS)
        self.assertEqual(len(PayPalIPN.objects.all()), 2)
        ipn_obj = PayPalIPN.objects.order_by('-created_at', '-pk')[0]
        self.assertEqual(ipn_obj.flag, True)
        self.assertEqual(ipn_obj.flag_info, "Duplicate txn_id. (51403485VH153354B)")

    def test_recurring_payment_skipped_ipn(self):
        update = {
            "recurring_payment_id": "BN5JZ2V7MLEV4",
            "txn_type": "recurring_payment_skipped",
            "txn_id": ""
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.assertGotSignal(recurring_skipped, False, params)

    def test_recurring_payment_failed_ipn(self):
        update = {
            "recurring_payment_id": "BN5JZ2V7MLEV4",
            "txn_type": "recurring_payment_failed",
            "txn_id": ""
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.assertGotSignal(recurring_failed, False, params)

    def test_recurring_payment_create_ipn(self):
        update = {
            "recurring_payment_id": "BN5JZ2V7MLEV4",
            "txn_type": "recurring_payment_profile_created",
            "txn_id": ""
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.assertGotSignal(recurring_create, False, params)

    def test_recurring_payment_cancel_ipn(self):
        update = {
            "recurring_payment_id": "BN5JZ2V7MLEV4",
            "txn_type": "recurring_payment_profile_cancel",
            "txn_id": ""
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.assertGotSignal(recurring_cancel, False, params)

    def test_recurring_payment_ipn(self):
        """
        The way the code is written in
        PayPalIPN.send_signals the recurring_payment
        will never be sent because the paypal ipn
        contains a txn_id, if this test fails you
        might break some compatibility
        """
        update = {
            "recurring_payment_id": "BN5JZ2V7MLEV4",
            "txn_type": "recurring_payment",
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.got_signal = False
        self.signal_obj = None

        def handle_signal(sender, **kwargs):
            self.got_signal = True
            self.signal_obj = sender
        recurring_payment.connect(handle_signal)

        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        ipns = PayPalIPN.objects.all()
        self.assertEqual(len(ipns), 1)
        self.assertFalse(self.got_signal)


    def test_refund_for_recurring_payment(self):
        update = {
            "payment_status": ST_PP_REFUNDED,
            "reason_code": "refund",
            "parent_txn_id": "1NK420530S625752Y",
            "recurring_payment_id": "I-N8KNB3KKD9NF"
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.assertGotSignal(recurring_refunded, False, params)


    def test_refund_for_non_recurring_payment(self):
        update = {
            "payment_status": ST_PP_REFUNDED,
            "reason_code": "refund",
            "parent_txn_id": "1NK420530S625752Y"
        }
        params = IPN_POST_PARAMS.copy()
        params.update(update)

        self.assertGotSignal(payment_refunded, False, params)


    # Subscription Tests

    def test_subscr_signup_ipn(self):
        params = IPN_SUBSCR_SIGNUP_PARAMS.copy()
        self.assertGotSignal(subscription_signup, False, params)

    def test_subscr_eot_ipn(self):
        params = IPN_SUBSCR_EOT_PARAMS.copy()
        self.assertGotSignal(subscription_eot, False, params)

    def test_subscr_failed_ipn(self):
        params = IPN_SUBSCR_FAILED_PARAMS.copy()
        self.assertGotSignal(subscription_failed, False, params)

    def test_subscr_cancel_ipn(self):
        params = IPN_SUBSCR_CANCEL_PARAMS.copy()
        self.assertGotSignal(subscription_cancel, False, params)

