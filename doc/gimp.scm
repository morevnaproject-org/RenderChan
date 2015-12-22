;; This is a human readable version of the script-fu code being run by though the batch argument of gimp
;; Empty lines separate output formats

; Unimplemented output formats: bz2, cel, csource, dds, dicom, eps, fits, fli, gbr, gih, gtm, gz, header, openraster, pat, ppm, pcx, pgm, pix, pnm, ppm, ps, sgi, uri, xbm, xwd, raw
; Implemented through general (no options): bmp, ico

; ASCII art (various)
; file-type options: Pure html, Text file, Nestcapeized html, ANSI escape sequences, vyhen, For more/less, HP laser jet - A4 small font, HP laser jet - A4 big font, For catting to an IRC Channel, For catting to an IRC Channel II, For including in a man page, HTML <IMG ALT= tag
; must be compiled with vyhen support to use the vyhen option 
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(file-aa-save RUN-NONINTERACTIVE image drawable outpath outpath <file-type>)
	(gimp-image-delete image)
)

; JPEG (.jpg)
; options: quality, smoothing, optimize, progressive, comment, subsmp, baseline, restart, dct
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(file-jpeg-save RUN-NONINTERACTIVE image drawable outpath outpath .9 0 0 0 " " 0 1 0 1)
	(gimp-image-delete image)
)

; PDF (.pdf)
; options: vectorize, ignore-hidden, apply-masks
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(file-pdf-save RUN-NONINTERACTIVE image drawable outpath outpath 0 1 1)
	(gimp-image-delete image)
)

; Portable network graphics (.png)
; options: interlace, compression, bkgd, gama, offs, phys, time, comment, svtrans
; TODO use default parameters found with file-png-get-defaults
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(file-png-save2 RUN-NONINTERACTIVE image drawable outpath outpath 0 9 0 0 0 1 0 0 0)
	(gimp-image-delete image)
)

; Photoshop document (.psd)
; options: compression, fill-order
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(file-psd-save RUN-NONINTERACTIVE image drawable outpath outpath 1 1)
	(gimp-image-delete image)
)

; TIFF (.tiff)
; options: compression, save-transp-pixels
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(file-tiff-save2 RUN-NONINTERACTIVE image drawable outpath outpath 1 0)
	(gimp-image-delete image)
)

; GIF (.gif)
; convert-indexed options: dither-type, palette-type, num-cols, alpha-dither, remove-unused, palette
; options: interlace, loop, default-delay, default-dispose
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-get-active-drawable image)))
	)
	
	(gimp-image-convert-indexed image 0 0 255 0 0 "")
	(file-gif-save RUN-NONINTERACTIVE image drawable outpath outpath 0 1 100 2)
	(gimp-image-delete image)
)

; Autodetect (.*)
; no options
(let*
	(
		(filename "<input>")
		(outpath "<output>")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-merge-visible-layers image CLIP-TO-IMAGE)))
	)
	
	(gimp-image-scale image width height)
	(gimp-file-save RUN-NONINTERACTIVE image drawable outpath outpath)
	(gimp-image-delete image)
)

; Motion PNG (.mng)
; options: interlace, compression, quality, smoothing, loop, default-delay, default-chunks, default-dispose, bkgd, gama, offs, phys, time, comment, svtrans
; TODO use default parameters found with file-png-get-defaults
(let*
	(
		(filename "<input>")
		(outpath "<output")
		(image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
		(drawable (car (gimp-image-get-active-drawable image)))
	)
	
	(file-mng-save RUN-NONINTERACTIVE image drawable outpath outpath 0 9 .9 0 1 100 2 1 0 0 1 0)
	(gimp-image-delete image)
)