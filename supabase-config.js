// Configurazione pubblica Supabase per ATELIER.
// La publishable key è destinata al browser; non inserire mai secret/service_role.
window.ATELIER_SUPABASE = {
  url: "https://bhbdrihvutdukrskrolj.supabase.co",
  anonKey: "sb_publishable_8xEo1Py4dKih3IALBGaJsQ_l35405vu"
};


// Preferenza globale del dispositivo: sessionStorage = uscita alla chiusura;
// localStorage = resta collegato. La scelta viene gestita dalle impostazioni account.
(() => {
  const authKey = 'sb-bhbdrihvutdukrskrolj-auth-token';
  const preferenceKey = 'atelier-remember-session';
  let remember = false;
  try { remember = localStorage.getItem(preferenceKey) === 'true'; } catch (_) {}

  function migrateSession() {
    try {
      const source = remember ? sessionStorage : localStorage;
      const target = remember ? localStorage : sessionStorage;
      const token = source.getItem(authKey) || target.getItem(authKey);
      if (token) target.setItem(authKey, token);
      source.removeItem(authKey);
    } catch (error) {
      console.warn('ATELIER: impossibile aggiornare la persistenza della sessione.', error);
    }
  }
  migrateSession();

  window.ATELIER_AUTH_STORAGE = {
    getItem(key) {
      try { return (remember ? localStorage : sessionStorage).getItem(key); }
      catch (_) { return null; }
    },
    setItem(key, value) {
      try {
        (remember ? localStorage : sessionStorage).setItem(key, value);
        (remember ? sessionStorage : localStorage).removeItem(key);
      } catch (error) {
        console.warn('ATELIER: impossibile salvare la sessione nel browser.', error);
      }
    },
    removeItem(key) {
      try { localStorage.removeItem(key); } catch (_) {}
      try { sessionStorage.removeItem(key); } catch (_) {}
    }
  };

  window.ATELIER_GET_REMEMBER = () => remember;
  window.ATELIER_SET_REMEMBER = value => {
    remember = Boolean(value);
    try { localStorage.setItem(preferenceKey, String(remember)); } catch (_) {}
    migrateSession();
  };
})();
