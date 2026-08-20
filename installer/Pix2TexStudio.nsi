Unicode true
ManifestDPIAware true
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetDatablockOptimize on

!define MUI_ICON "..\packaging\pix2tex-studio.ico"
!define MUI_UNICON "..\packaging\pix2tex-studio.ico"
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

Var ReleaseTest

Function .onInit
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/RELEASETEST" $R1
  ${IfNot} ${Errors}
    StrCpy $ReleaseTest 1
  ${EndIf}
FunctionEnd

Function un.onInit
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/RELEASETEST" $R1
  ${IfNot} ${Errors}
    StrCpy $ReleaseTest 1
  ${EndIf}
FunctionEnd

!define APP_NAME "Pix2Tex Studio"
!define APP_VERSION "2.0.0-rc1"
!define APP_PUBLISHER "Reasonix"
!define APP_EXE "Pix2TexStudio.exe"
!define APP_REG_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pix2TexStudio"

Name "${APP_NAME}"
OutFile "output\Pix2TexStudio-${APP_VERSION}-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Pix2Tex Studio"
InstallDirRegKey HKCU "${APP_REG_KEY}" "InstallLocation"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "运行 Pix2Tex Studio"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Section "Pix2Tex Studio" MainSection
  SectionIn RO
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "..\dist\Pix2TexStudio\*.*"
  File /oname=pix2tex.ico "..\packaging\pix2tex-studio.ico"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  ${If} $ReleaseTest != 1
    CreateDirectory "$SMPROGRAMS\Pix2Tex Studio"
    CreateShortcut "$SMPROGRAMS\Pix2Tex Studio\Pix2Tex Studio.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\pix2tex.ico" 0
    CreateShortcut "$SMPROGRAMS\Pix2Tex Studio\卸载 Pix2Tex Studio.lnk" "$INSTDIR\Uninstall.exe"
    Delete "$DESKTOP\Pix2Tex Studio.lnk"
    CreateShortcut "$DESKTOP\pix2tex.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\pix2tex.ico" 0

    WriteRegStr HKCU "${APP_REG_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "${APP_REG_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "${APP_REG_KEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKCU "${APP_REG_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKCU "${APP_REG_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "${APP_REG_KEY}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKCU "${APP_REG_KEY}" "QuietUninstallString" "$\"$INSTDIR\Uninstall.exe$\" /S"
    WriteRegDWORD HKCU "${APP_REG_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${APP_REG_KEY}" "NoRepair" 1
  ${EndIf}
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  ${If} $ReleaseTest != 1
    Delete "$DESKTOP\pix2tex.lnk"
    Delete "$DESKTOP\Pix2Tex Studio.lnk"
    Delete "$SMPROGRAMS\Pix2Tex Studio\Pix2Tex Studio.lnk"
    Delete "$SMPROGRAMS\Pix2Tex Studio\卸载 Pix2Tex Studio.lnk"
    RMDir "$SMPROGRAMS\Pix2Tex Studio"
    DeleteRegKey HKCU "${APP_REG_KEY}"
  ${EndIf}
  RMDir /r "$INSTDIR"
SectionEnd
