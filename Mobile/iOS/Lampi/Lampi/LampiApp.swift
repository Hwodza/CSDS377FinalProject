//
//  LampiApp.swift
//  Lampi
//

import SwiftUI

@main
struct LampiApp: App {
    #warning("Update DEVICE_NAME")
    let DEVICE_NAME = "LAMPI XXXXXXX"
    let USE_BROWSER = false

    var body: some Scene {
        WindowGroup {
            if USE_BROWSER {
                LampiBrowserView()
            } else {
                LampiView(lamp: Lampi(name: DEVICE_NAME))
            }
        }
    }
}
