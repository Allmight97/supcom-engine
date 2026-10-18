import CoreGraphics
// usage: winid [OWNER] [--all]   (--all also lists windows that are not on screen, e.g. on another Space)
let args = CommandLine.arguments.dropFirst()
let wanted = args.first(where: { $0 != "--all" }) ?? "SupremeCommander"
let opts: CGWindowListOption = args.contains("--all") ? .optionAll : .optionOnScreenOnly
for w in (CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]]) ?? [] {
    let owner = w[kCGWindowOwnerName as String] as? String ?? ""
    let layer = w[kCGWindowLayer as String] as? Int ?? 0
    if owner.contains(wanted) && layer < 1000 && !(w[kCGWindowName as String] as? String ?? "").isEmpty {
        let b = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
        print(w[kCGWindowNumber as String] ?? "", w[kCGWindowOwnerPID as String] ?? "", owner, w[kCGWindowName as String] ?? "", b["X"] ?? "", b["Y"] ?? "", b["Width"] ?? "", b["Height"] ?? "")
    }
}
