import Foundation
import Vision
import CoreImage

let input = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
let handler = VNImageRequestHandler(url: input)
let request = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([request])
guard let result = request.results?.first else {
  FileHandle.standardError.write("no subject found\n".data(using: .utf8)!)
  exit(1)
}
let buffer = try result.generateMaskedImage(
  ofInstances: result.allInstances, from: handler, croppedToInstancesExtent: false)
let image = CIImage(cvPixelBuffer: buffer)
try CIContext().writePNGRepresentation(
  of: image, to: output, format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
print("instances:", result.allInstances.count)
