package com.braniac.app;

import android.app.Activity;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;

/** Libera o microfone so para a nossa propria pagina (origem https://braniac.local); qualquer outra origem e negada.
 *  Sem classes internas/lambdas de proposito: o d8 do build-tools 34 quebra com as de classes compiladas pelo JDK 26. */
public class Chrome extends WebChromeClient {
    private final Activity act;

    public Chrome(Activity a) {
        act = a;
    }

    @Override
    public void onPermissionRequest(PermissionRequest r) {
        act.runOnUiThread(new Decide(r));
    }
}
