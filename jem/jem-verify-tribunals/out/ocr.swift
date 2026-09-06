import Foundation
import PDFKit
import Vision
import AppKit

let path = CommandLine.arguments[1]
let destination = CommandLine.arguments[2]
let document = PDFDocument(url: URL(fileURLWithPath: path))!
var output = ""
for index in 0..<document.pageCount {
    autoreleasepool {
        let page = document.page(at: index)!
        let thumb = page.thumbnail(of: NSSize(width: 1600, height: 2200), for: .mediaBox)
        var rectangle = CGRect(origin: .zero, size: thumb.size)
        guard let image = thumb.cgImage(forProposedRect: &rectangle, context: nil, hints: nil) else { return }
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["en-US"]
        request.usesLanguageCorrection = false
        do {
            try VNImageRequestHandler(cgImage: image).perform([request])
            output += "\n[PDF page \(index + 1), OCR]\n"
            for observation in request.results ?? [] {
                if let result = observation.topCandidates(1).first {
                    output += result.string + "\n"
                }
            }
            try output.write(toFile: destination, atomically: true, encoding: .utf8)
            print("OCR page \(index + 1)/\(document.pageCount)")
        } catch {
            print("OCR failed page \(index + 1): \(error)")
        }
    }
}
