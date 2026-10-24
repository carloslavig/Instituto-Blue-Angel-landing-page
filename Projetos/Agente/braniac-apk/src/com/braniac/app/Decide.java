package com.braniac.app;

import android.webkit.PermissionRequest;

public class Decide implements Runnable {
    private final PermissionRequest r;

    public Decide(PermissionRequest r) {
        this.r = r;
    }

    public void run() {
        if (r.getOrigin().toString().startsWith("https://braniac.local")) r.grant(r.getResources());
        else r.deny();
    }
}
