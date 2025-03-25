//
//  LampiView.swift
//  Lampi
//

import SwiftUI

struct LampiView: View {
    @Bindable var lamp: Lampi

    @Environment(\.presentationMode) var mode: Binding<PresentationMode>

    var body: some View {
        VStack {
            ZStack(alignment: .bottom) {
                Rectangle()
                    .fill(lamp.state.color)
                    .edgesIgnoringSafeArea(.top)
                Text("\(lamp.state.isConnected ? "Connected" : "Disconnected")")
                    .foregroundColor(.white)
                    .padding()
                    .background(RoundedRectangle(cornerRadius: .infinity)
                                    .fill(Color(white: 0.25, opacity: 0.5)))
                    .padding()
            }

            VStack(alignment: .center, spacing: 20) {
                GradientSlider(value: $lamp.state.hue,
                               handleColor: lamp.state.baseHueColor,
                               trackColors: Color.rainbow())

                GradientSlider(value: $lamp.state.saturation,
                               handleColor: Color(hue: lamp.state.hue,
                                                  saturation: lamp.state.saturation,
                                                  brightness: 1.0),
                               trackColors: [.white, lamp.state.baseHueColor])

                GradientSlider(value: $lamp.state.brightness,
                               handleColor: Color(white: lamp.state.brightness),
                               handleImage: Image(systemName: "sun.max"),
                               trackColors: [.black, .white])
                    .foregroundColor(Color(white: 1.0 - lamp.state.brightness))
            }.padding(.horizontal)

            Button(action: {
                lamp.state.isOn = !lamp.state.isOn
            }) {
                HStack {
                    Spacer()
                    Image(systemName: "power")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                    Spacer()
                }.padding()
            }
            .foregroundColor(lamp.state.isOn ? lamp.state.color : .gray)
            .background(Color.black.edgesIgnoringSafeArea(.bottom))
            .frame(height: 100)
        }
        .disabled(!lamp.state.isConnected)
        .navigationBarBackButtonHidden(true)
        .navigationBarItems(leading: Button(action : {
            self.mode.wrappedValue.dismiss()
        }){
            Image(systemName: "arrow.left")
                .foregroundColor(.white)
                .shadow(radius: 2.0)
        })
    }
}

#Preview {
    LampiView(lamp: Lampi(name: "LAMPI b827ebccda1f"))
        .previewDevice("iPhone 15 Pro")
        .previewLayout(.device)
}
