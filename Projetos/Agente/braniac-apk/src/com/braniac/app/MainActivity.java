package com.braniac.app;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.content.pm.PackageManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/** B.R.A.N.I.A.C no celular: uma WebView que abre a tela de conexao (assets/index.html), que fala P2P (WebRTC) com o Braniac do notebook. */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        Window w = getWindow();
        w.setStatusBarColor(Color.parseColor("#050d14"));
        w.setNavigationBarColor(Color.parseColor("#050d14"));
        w.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#050d14"));
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, 1);
        web.setWebChromeClient(new Chrome(this));
        try {
            InputStream in = getAssets().open("index.html");
            ByteArrayOutputStream o = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) o.write(buf, 0, n);
            in.close();
            // origem https (contexto seguro): WebCrypto, WebRTC e localStorage funcionam
            web.loadDataWithBaseURL("https://braniac.local/", o.toString("UTF-8"), "text/html", "utf-8", null);
        } catch (Exception e) {
            web.loadData("Falha ao abrir o app: " + e, "text/plain", "utf-8");
        }
    }

    @Override
    public void onBackPressed() {
        moveTaskToBack(true);
    }
}
