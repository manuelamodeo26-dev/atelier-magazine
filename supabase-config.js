// Configurazione pubblica Supabase per ATELIER.
// La publishable key è destinata al browser; non inserire mai secret/service_role.
window.ATELIER_SUPABASE = {
  url: "https://bhbdrihvutdukrskrolj.supabase.co",
  anonKey: "sb_publishable_8xEo1Py4dKih3IALBGaJsQ_l35405vu"
};


// Preferenza "Resta collegato": sessionStorage mantiene l'accesso solo nella sessione
// corrente; localStorage lo conserva anche dopo la chiusura del browser.
(() => {
  let remember = false;
  const authKey = 'sb-bhbdrihvutdukrskrolj-auth-token';
  const storage = {
    getItem(key) {
      try { return localStorage.getItem(key) ?? sessionStorage.getItem(key); }
      catch (_) { return null; }
    },
    setItem(key, value) {
      try {
        if (remember) {
          localStorage.setItem(key, value);
          sessionStorage.removeItem(key);
        } else {
          sessionStorage.setItem(key, value);
          localStorage.removeItem(key);
        }
      } catch (error) {
        console.warn('ATELIER: impossibile salvare la sessione nel browser.', error);
      }
    },
    removeItem(key) {
      try { localStorage.removeItem(key); } catch (_) {}
      try { sessionStorage.removeItem(key); } catch (_) {}
    }
  };
  window.ATELIER_AUTH_STORAGE = storage;
  window.ATELIER_SET_REMEMBER = value => {
    remember = Boolean(value);
    try {
      const current = remember
        ? sessionStorage.getItem(authKey)
        : localStorage.getItem(authKey);
      if (current) {
        (remember ? localStorage : sessionStorage).setItem(authKey, current);
        (remember ? sessionStorage : localStorage).removeItem(authKey);
      }
    } catch (_) {}
  };
})();
