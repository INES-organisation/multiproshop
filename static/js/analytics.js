/**
 * Mesure d'audience et pixels publicitaires (GA4, Meta, TikTok), chargés seulement après accord.
 * Les pages appellent mpsTrack(événement, données) ; sans accord, rien ne part.
 * Événements : view_item, add_to_cart, begin_checkout, purchase (noms GA4, traduits pour Meta et TikTok).
 */
(function () {
    const config = window.MPS_ANALYTICS || {};
    const KEY = 'mps_consent';
    const queue = [];
    let loaded = false;

    function stored() {
        try { return localStorage.getItem(KEY); } catch (e) { return null; }
    }

    function store(value) {
        try { localStorage.setItem(KEY, value); } catch (e) { /* navigation privée : on redemandera */ }
    }

    function loadScript(src) {
        const s = document.createElement('script');
        s.async = true;
        s.src = src;
        document.head.appendChild(s);
    }

    function load() {
        if (loaded) return;
        loaded = true;
        if (config.ga4) {
            window.dataLayer = window.dataLayer || [];
            window.gtag = function () { dataLayer.push(arguments); };
            gtag('js', new Date());
            gtag('config', config.ga4, { anonymize_ip: true });
            loadScript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(config.ga4));
        }
        if (config.meta) {
            const fbq = window.fbq = function () {
                fbq.callMethod ? fbq.callMethod.apply(fbq, arguments) : fbq.queue.push(arguments);
            };
            if (!window._fbq) window._fbq = fbq;
            fbq.push = fbq; fbq.loaded = true; fbq.version = '2.0'; fbq.queue = [];
            loadScript('https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', config.meta);
            fbq('track', 'PageView');
        }
        if (config.tiktok) {
            const ttq = window.ttq = window.ttq || [];
            ttq.methods = ['page', 'track', 'identify', 'instances', 'debug', 'on', 'off', 'once', 'ready', 'alias', 'group', 'enableCookie', 'disableCookie'];
            ttq.setAndDefer = function (t, e) { t[e] = function () { t.push([e].concat(Array.prototype.slice.call(arguments, 0))); }; };
            ttq.methods.forEach(function (m) { ttq.setAndDefer(ttq, m); });
            loadScript('https://analytics.tiktok.com/i18n/pixel/events.js?sdkid=' + encodeURIComponent(config.tiktok) + '&lib=ttq');
            ttq.page();
        }
        queue.splice(0).forEach(function (e) { send(e[0], e[1]); });
    }

    const META_EVENTS = { view_item: 'ViewContent', add_to_cart: 'AddToCart', begin_checkout: 'InitiateCheckout', purchase: 'Purchase' };
    const TIKTOK_EVENTS = { view_item: 'ViewContent', add_to_cart: 'AddToCart', begin_checkout: 'InitiateCheckout', purchase: 'CompletePayment' };

    function send(event, data) {
        data = Object.assign({ currency: 'EUR' }, data);
        const ids = (data.items || []).map(function (i) { return String(i.item_id); });
        if (window.gtag) gtag('event', event, data);
        if (window.fbq && META_EVENTS[event]) {
            fbq('track', META_EVENTS[event], { value: data.value, currency: data.currency, content_ids: ids, content_type: 'product' },
                data.transaction_id ? { eventID: data.transaction_id } : undefined);
        }
        if (window.ttq && TIKTOK_EVENTS[event]) {
            ttq.track(TIKTOK_EVENTS[event], {
                value: data.value, currency: data.currency,
                contents: (data.items || []).map(function (i) { return { content_id: String(i.item_id), content_name: i.item_name, quantity: i.quantity, price: i.price }; })
            });
        }
    }

    window.mpsTrack = function (event, data) {
        if (stored() !== 'granted') return;
        loaded ? send(event, data) : queue.push([event, data]);
    };

    function banner() { return document.getElementById('consent-banner'); }

    function choose(value) {
        store(value);
        const b = banner();
        if (b) b.hidden = true;
        if (value === 'granted') load();
    }

    window.mpsOpenConsent = function () {
        const b = banner();
        if (b) b.hidden = false;
    };

    document.addEventListener('DOMContentLoaded', function () {
        const b = banner();
        if (!b) return;
        b.querySelector('[data-consent="granted"]').addEventListener('click', function () { choose('granted'); });
        b.querySelector('[data-consent="denied"]').addEventListener('click', function () { choose('denied'); });
        const choice = stored();
        if (choice === 'granted') load();
        else if (!choice) b.hidden = false;
    });
})();
