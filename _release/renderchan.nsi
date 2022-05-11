;--------------------------------
; Requires files:
;   config.nsh
;   files-install.nsh
;   files-ffmpeg-install.nsh
;   files-examples-install.nsh
;   files-uninstall.nsh

; Defines which will set by 'config.nsh':
;   PK_NAME          - XxxxxXxxxx               - name without spaces 
;   PK_DIR_NAME      - Xxxxx Xxxxx              - dir name, may be with spaces 
;   PK_NAME_FULL     - Xxxxx Xxxxxxxxxx         - full name, may be with spaces
;   PK_ARCH          - XX                       - architecture, 32 or 64
;   PK_VERSION       - X.X                      - first two numbers of version
;   PK_VERSION_FULL  - X.X.X-xxxxx-xxxxx        - full version, without spaces 
;   PK_EXECUTABLE    - xxx\XxxxXxxx-xxx_xxx.exe - subpath to executable file 
;   PK_ICON          - xxx\XxxxXxxx-xxx_xxx.ico - subpath to icon file (may be *.exe)
;   PK_LICENSE       - xxxxxxxx\xxxxxxx-xxx.txt - subpath to license file

!include "config.nsh"

;--------------------------------

!include "MUI2.nsh"

;--------------------------------

; The name of the installer
Name "${PK_NAME_FULL} ${PK_VERSION_FULL}"

; The file to write
OutFile "${PK_NAME}-${PK_VERSION_FULL}.exe"

; The default installation directory and registry
InstallDir "$PROGRAMFILES${PK_ARCH}\${PK_DIR_NAME}"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

!define MUI_ABORTWARNING

!define SHCNE_ASSOCCHANGED 0x8000000
!define SHCNF_IDLIST 0

!define PRODUCT_REG_KEY "Software\${PK_NAME}"
!define PRODUCT_UNINSTALL_KEY  "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PK_NAME}"
!define PRODUCT_UNINSTALL_EXE  "uninstall-${PK_NAME}.exe"

;--------------------------------

; Pages

!insertmacro MUI_PAGE_LICENSE ".\${PK_LICENSE}"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer
;--------------------------------

Section "${PK_NAME_FULL} (required)"
  SetRegView ${PK_ARCH}

  SectionIn RO

  SetOutPath "$INSTDIR"
  !include "files-install.nsh"
  
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "Path" "$INSTDIR"
  WriteRegStr HKLM "${PRODUCT_REG_KEY}" "Version" "${PK_VERSION_FULL}"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "${PRODUCT_UNINSTALL_KEY}" "DisplayName" "${PK_NAME_FULL}"
  WriteRegStr HKLM "${PRODUCT_UNINSTALL_KEY}" "DisplayVersion" "${PK_VERSION_FULL}"
  WriteRegStr HKLM "${PRODUCT_UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\${PRODUCT_UNINSTALL_EXE}"'
  WriteRegDWORD HKLM "${PRODUCT_UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${PRODUCT_UNINSTALL_KEY}" "NoRepair" 1

  System::Call 'Shell32::SHChangeNotify(i ${SHCNE_ASSOCCHANGED}, i ${SHCNF_IDLIST}, i 0, i 0)'

  SetOutPath "$INSTDIR"
  WriteUninstaller "${PRODUCT_UNINSTALL_EXE}"
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"
  SetRegView ${PK_ARCH}

  SetOutPath "$INSTDIR"

  SetShellVarContext All
  CreateDirectory "$SMPROGRAMS\${PK_DIR_NAME}"
  CreateShortCut "$SMPROGRAMS\${PK_DIR_NAME}\Uninstall ${PK_NAME_FULL}.lnk" "$INSTDIR\uninstall-${PK_NAME}.exe" "" "$INSTDIR\uninstall-${PK_NAME}.exe" 0
  CreateShortCut "$SMPROGRAMS\${PK_DIR_NAME}\${PK_NAME_FULL}.lnk" "$INSTDIR\${PK_EXECUTABLE}" "" "$INSTDIR\${PK_ICON}" 0
SectionEnd

Section "Desktop Icon"
  SetRegView ${PK_ARCH}

  SetOutPath "$INSTDIR"

  SetShellVarContext All
  CreateShortCut "$DESKTOP\${PK_NAME_FULL}.lnk" "$INSTDIR\${PK_EXECUTABLE}" "" "$INSTDIR\${PK_ICON}" 0
SectionEnd

;--------------------------------
; Uninstaller
;--------------------------------

Section "Uninstall"
  SetRegView ${PK_ARCH}

  ReadRegStr $INSTDIR HKLM "${PRODUCT_REG_KEY}" "Path"

  ; Remove registry keys
  DeleteRegKey HKLM "${PRODUCT_REG_KEY}"
  DeleteRegKey HKLM "${PRODUCT_UNINSTALL_KEY}"

  ; Remove files and uninstaller
  !include "files-uninstall.nsh"
  Delete "$INSTDIR\${PRODUCT_UNINSTALL_EXE}"

  ; Remove shortcuts, if any
  SetShellVarContext All
  Delete "$DESKTOP\${PK_NAME_FULL}.lnk"
  Delete "$SMPROGRAMS\${PK_DIR_NAME}\${PK_NAME_FULL}.lnk"
  Delete "$SMPROGRAMS\${PK_DIR_NAME}\Uninstall ${PK_NAME_FULL}.lnk"

  ; Remove directories used
  RMDir "$SMPROGRAMS\${PK_DIR_NAME}"
  RMDir "$INSTDIR"

  System::Call 'Shell32::SHChangeNotify(i ${SHCNE_ASSOCCHANGED}, i ${SHCNF_IDLIST}, i 0, i 0)'
SectionEnd

Function .onInit
  ; Check previous installation

  SetRegView ${PK_ARCH}
  ReadRegStr $R0 HKLM "${PRODUCT_UNINSTALL_KEY}" "UninstallString"
  StrCmp $R0 "" 0 oops
  
  SetRegView 32
  ReadRegStr $R0 HKLM "${PRODUCT_UNINSTALL_KEY}" "UninstallString"
  StrCmp $R0 "" 0 oops

  SetRegView 64
  ReadRegStr $R0 HKLM "${PRODUCT_UNINSTALL_KEY}" "UninstallString"
  StrCmp $R0 "" 0 oops

  BringToFront
  Return

oops:
  MessageBox MB_YESNOCANCEL|MB_ICONEXCLAMATION "Another version of this software appears to be installed. Would you like to uninstall it first?" IDNO ignore IDCANCEL cancel
  ExecWait '$R0'
  BringToFront
  Return

cancel:
  MessageBox MB_OK|MB_ICONEXCLAMATION "Unable to uninstall another version of RenderChan"
  Abort

ignore:
  BringToFront
  Return
FunctionEnd
