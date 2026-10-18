import CoreGraphics
import Foundation
setvbuf(stdout, nil, _IOLBF, 0)
func gamePid() -> Int32? {
    let p = Process(); p.executableURL = URL(fileURLWithPath: "/usr/bin/pgrep"); p.arguments = ["-f", "ForgedAlliance[.]exe|SupremeCommander[.]exe"]
    let o = Pipe(); p.standardOutput = o; try? p.run(); p.waitUntilExit()
    let s = String(data: o.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
    return s.split(separator: "\n").compactMap { Int32($0) }.first
}
var last = ""
while true {
    let t = String(format: "%.1f", Date().timeIntervalSince1970)
    let c = CGEvent(source: nil)?.location ?? .zero
    let d = CGMainDisplayID(); let m = CGDisplayCopyDisplayMode(d)
    var win = "nowin"
    if let pid = gamePid() {
        // Wine windows belong to the wine-preloader process; match any window whose owner pid has the game exe, else by owner name
        for w in (CGWindowListCopyWindowInfo(.optionOnScreenOnly, kCGNullWindowID) as? [[String: Any]]) ?? [] {
            let wp = w[kCGWindowOwnerPID as String] as? Int32 ?? 0
            let owner = w[kCGWindowOwnerName as String] as? String ?? ""
            guard wp == pid || owner.contains("ForgedAlliance") || owner.contains("SupremeCommander") else { continue }
            let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
            let layer = w[kCGWindowLayer as String] as? Int ?? 0
            let bw = b["Width"] as? Double ?? 0
            if bw < 200 { continue }
            win = "win \(b["X"] ?? 0),\(b["Y"] ?? 0) \(b["Width"] ?? 0)x\(b["Height"] ?? 0) layer \(layer) owner \(owner)"
            break
        }
        if win == "nowin" { win = "pid \(pid) nowin" }
    }
    let mode = "mode \(m?.width ?? 0)x\(m?.height ?? 0) px \(m?.pixelWidth ?? 0)x\(m?.pixelHeight ?? 0)"
    let state = "\(mode) \(win)"
    print("\(t) cursor \(Int(c.x)),\(Int(c.y)) \(state)\(state == last ? "" : "  <-- changed")")
    last = state
    Thread.sleep(forTimeInterval: 0.2)
}
