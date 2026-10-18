import CoreGraphics
import Foundation
import AppKit
import ApplicationServices
// usage: input activate NAME|PID | input click X Y [right] | input move X Y | input key KEYCODE | input drag X1 Y1 X2 Y2 | input scroll X Y LINES | input type TEXT
// GUARD_PID=PID refuses each event unless that process is frontmost.
let a = CommandLine.arguments
let guardPID = ProcessInfo.processInfo.environment["GUARD_PID"].flatMap { Int32($0) }
func post(_ e: CGEvent?) {
    if let pid = guardPID, NSWorkspace.shared.frontmostApplication?.processIdentifier != pid {
        print("refused: target lost focus (front: \(NSWorkspace.shared.frontmostApplication?.localizedName ?? "none"))")
        exit(3)
    }
    e?.post(tap: .cghidEventTap); usleep(30000)
}
let src = CGEventSource(stateID: .hidSystemState)
switch a[1] {
case "activate":
    let wanted = a[2]
    guard let app = NSWorkspace.shared.runningApplications.first(where: {
        if let pid = Int32(wanted) { return $0.processIdentifier == pid }
        return ($0.localizedName ?? "").contains(wanted) || ($0.executableURL?.lastPathComponent ?? "").contains(wanted)
    }) else { print("no process \(wanted)"); exit(1) }
    let element = AXUIElementCreateApplication(app.processIdentifier)
    var windows: CFTypeRef?
    if AXUIElementCopyAttributeValue(element, kAXWindowsAttribute as CFString, &windows) == .success,
       let window = (windows as? [AXUIElement])?.first {
        AXUIElementSetAttributeValue(window, kAXMinimizedAttribute as CFString, kCFBooleanFalse)
        AXUIElementPerformAction(window, kAXRaiseAction as CFString)
    }
    AXUIElementSetAttributeValue(element, kAXFrontmostAttribute as CFString, kCFBooleanTrue)
    app.activate(options: [.activateIgnoringOtherApps])
    for _ in 0..<20 {
        if NSWorkspace.shared.frontmostApplication?.processIdentifier == app.processIdentifier { break }
        usleep(100000)
    }
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == app.processIdentifier else {
        print("refused: \(wanted) is not frontmost (front: \(NSWorkspace.shared.frontmostApplication?.localizedName ?? "none"))")
        exit(3)
    }
case "move":
    post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: CGPoint(x: Double(a[2])!, y: Double(a[3])!), mouseButton: .left))
case "click":
    let p = CGPoint(x: Double(a[2])!, y: Double(a[3])!)
    let right = a.count > 4 && a[4] == "right"
    post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left))
    usleep(150000)
    post(CGEvent(mouseEventSource: src, mouseType: right ? .rightMouseDown : .leftMouseDown, mouseCursorPosition: p, mouseButton: right ? .right : .left))
    usleep(80000)
    post(CGEvent(mouseEventSource: src, mouseType: right ? .rightMouseUp : .leftMouseUp, mouseCursorPosition: p, mouseButton: right ? .right : .left))
case "drag":
    let p1 = CGPoint(x: Double(a[2])!, y: Double(a[3])!), p2 = CGPoint(x: Double(a[4])!, y: Double(a[5])!)
    post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: p1, mouseButton: .left))
    post(CGEvent(mouseEventSource: src, mouseType: .leftMouseDown, mouseCursorPosition: p1, mouseButton: .left))
    for i in 1...10 { let t = Double(i) / 10; post(CGEvent(mouseEventSource: src, mouseType: .leftMouseDragged, mouseCursorPosition: CGPoint(x: p1.x + (p2.x - p1.x) * t, y: p1.y + (p2.y - p1.y) * t), mouseButton: .left)) }
    post(CGEvent(mouseEventSource: src, mouseType: .leftMouseUp, mouseCursorPosition: p2, mouseButton: .left))
case "scroll":
    post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: CGPoint(x: Double(a[2])!, y: Double(a[3])!), mouseButton: .left))
    let lines = Int32(a[4])!
    for _ in 0..<abs(lines) { post(CGEvent(scrollWheelEvent2Source: src, units: .line, wheelCount: 1, wheel1: lines < 0 ? -1 : 1, wheel2: 0, wheel3: 0)) }
case "key":
    let k = CGKeyCode(Int(a[2])!)
    post(CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: true))
    post(CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: false))
case "type":
    let codes: [Character: CGKeyCode] = ["a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
        "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "1": 18, "2": 19, "3": 20, "4": 21, "6": 22,
        "5": 23, "9": 25, "7": 26, "8": 28, "0": 29, "o": 31, "u": 32, "i": 34, "p": 35, "l": 37, "j": 38, "k": 40,
        "n": 45, "m": 46, " ": 49, "-": 27]
    for ch in a[2].lowercased() {
        guard let k = codes[ch] else { print("cannot type", ch); exit(1) }
        post(CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: true))
        post(CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: false))
        usleep(70000)
    }
default: print("unknown")
}
print("ok", AXIsProcessTrusted() ? "accessibility-trusted" : "NOT-trusted")
