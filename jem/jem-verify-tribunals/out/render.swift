import Foundation
import PDFKit
import AppKit

let document = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
let page = document.page(at: Int(CommandLine.arguments[2])! - 1)!
let image = page.thumbnail(of: NSSize(width: 1800, height: 2400), for: .mediaBox)
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
let data = bitmap.representation(using: .png, properties: [:])!
try data.write(to: URL(fileURLWithPath: CommandLine.arguments[3]))
