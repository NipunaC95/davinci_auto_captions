--[[
Auto Caption Studio for DaVinci Resolve Free v21
Native Lua Script & UI Panel using UIManager
--]]

local ui = fusion.UIManager
local disp = bmd.UIDispatcher(ui)

local winID = "com.autocaption.resolve.LuaPanel"
local existing_win = ui:FindWindow(winID)
if existing_win then
    existing_win:Show()
    existing_win:Raise()
    return
end

local project_dir = "__AUTO_CAPTION_PROJECT_DIR__"
local is_windows = package.config:sub(1, 1) == "\\"
local venv_py = project_dir .. (is_windows and "/venv/Scripts/python.exe" or "/venv/bin/python3")
local quick_caption_cli = project_dir .. "/core/quick_caption.py"

-- Query current project and timeline
local pm = resolve and resolve:GetProjectManager()
local proj = pm and pm:GetCurrentProject()
local timeline = proj and proj:GetCurrentTimeline()
local timeline_name = timeline and timeline:GetName() or "No Timeline Open"

local found_media = {}
if timeline then
    local types = {"video", "audio"}
    for _, t_type in ipairs(types) do
        local count = timeline:GetTrackCount(t_type) or 0
        for idx = 1, count do
            local items = timeline:GetItemListInTrack(t_type, idx) or {}
            for _, item in ipairs(items) do
                local mp_item = item:GetMediaPoolItem()
                if mp_item then
                    local props = mp_item:GetClipProperty()
                    local fp = props and props["File Path"] or ""
                    if fp and fp ~= "" and not found_media[fp] then
                        found_media[#found_media + 1] = fp
                        found_media[fp] = true
                    end
                end
            end
        end
    end
end

local active_file = found_media[1] or ""
local media_display = active_file ~= "" and string.match(active_file, "[^/]+$") or "None (Click 'Browse Media...')"

local styles = {
    "Hormozi Viral",
    "TikTok Bounce",
    "MrBeast Highlighter",
    "Cinematic Box",
    "Cyber Neon",
    "Clean Minimalist",
    "Retro Comic Pop",
    "Split Tone"
}

local style_descs = {
    ["Hormozi Viral"] = "Bold yellow viral text with thick black outline, drop shadow, and pop bounce",
    ["TikTok Bounce"] = "High contrast white text with solid black stroke and dynamic bounce pop",
    ["MrBeast Highlighter"] = "Electric neon lime-green text with heavy comic outline and hard drop shadow",
    ["Cinematic Box"] = "Clean modern sans-serif typography inside a rounded dark translucent box",
    ["Cyber Neon"] = "Futuristic electric cyan with dual glowing outline and ambient magenta backlight",
    ["Clean Minimalist"] = "Crisp white subtitle with soft diffused ambient shadow for interviews",
    ["Retro Comic Pop"] = "Golden yellow text with black border and 3D extruded red shadow offset",
    ["Split Tone"] = "Gold-to-white gradient with high-contrast dark border"
}

local header_html = [[
<html><body>
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <h2 style="color:#F3A63B; margin:0; padding:0;">⚡ Auto Caption Studio</h2>
      <p style="color:#A0A0B0; margin:2px 0 0 0; font-size:11px;">Native DaVinci Resolve Free v21 Caption & Title Panel</p>
    </td>
  </tr>
</table>
</body></html>
]]

local win = disp:AddWindow({
    ID = winID,
    Geometry = { 250, 180, 560, 520 },
    WindowTitle = "⚡ Auto Caption Studio — DaVinci Resolve Panel",
},
ui:VGroup({ Spacing = 8, Margin = 15 }, {
    ui:Label({ Text = header_html, Weight = 0 }),
    ui:VGap(2),

    -- Section 1: Active Timeline & Media
    ui:Label({ Text = "<b>1. Timeline Source Audio</b>", Weight = 0 }),
    ui:HGroup({ Weight = 0 }, {
        ui:LineEdit({ ID = "FileBox", Text = active_file, PlaceholderText = "Click Browse or fetch from timeline...", ReadOnly = true, Weight = 0.8 }),
        ui:Button({ ID = "BrowseBtn", Text = "Browse...", Weight = 0.2 }),
    }),
    ui:Label({ ID = "TimelineStatus", Text = '<small style="color:#10B981;">● Active Timeline: ' .. timeline_name .. " (" .. #found_media .. " media clips detected)</small>", Weight = 0 }),
    ui:Button({ ID = "RefreshTimelineBtn", Text = "↻ Refresh Active Timeline", Weight = 0 }),
    ui:VGap(4),

    -- Section 2: Style Preset Picker
    ui:Label({ Text = "<b>2. Select Caption Style (Drag-and-Drop Preset)</b>", Weight = 0 }),
    ui:ComboBox({ ID = "StyleCombo", Weight = 0 }),
    ui:Label({ ID = "StyleDesc", Text = '<small style="color:#A0A0B0;">' .. style_descs["Hormozi Viral"] .. "</small>", Weight = 0 }),
    ui:VGap(4),

    -- Section 3: Timing & Layout
    ui:Label({ Text = "<b>3. Caption Timing & Length</b>", Weight = 0 }),
    ui:HGroup({ Weight = 0 }, {
        ui:VGroup({ Weight = 0.5 }, {
            ui:Label({ Text = "<small>Words per Clip:</small>", Weight = 0 }),
            ui:ComboBox({ ID = "ChunkCombo", Weight = 0 }),
        }),
        ui:VGroup({ Weight = 0.5 }, {
            ui:Label({ Text = "<small>Whisper AI Model:</small>", Weight = 0 }),
            ui:ComboBox({ ID = "ModelCombo", Weight = 0 }),
        }),
    }),
    ui:VGap(8),

    -- Progress / Status Box
    ui:Label({ ID = "StatusMsg", Text = '<span style="color:#E0E0E6;">Ready. Click Auto-Caption to transcribe timeline speech.</span>', Weight = 0 }),

    -- Action Buttons
    ui:VGap(4),
    ui:Button({ ID = "ActionBtn", Text = "⚡ AUTO-CAPTION TIMELINE NOW", Weight = 0 }),
    ui:Button({ ID = "CloseBtn", Text = "Close Panel", Weight = 0 }),
}))

local items = win:GetItems()

for _, s in ipairs(styles) do
    items.StyleCombo:AddItem(s)
end

local chunks = {
    "short (2-3 words, TikTok/Reels)",
    "1_word (Punchy)",
    "balanced (4-6 words)",
    "sentence (Full Sentences)"
}
for _, c in ipairs(chunks) do
    items.ChunkCombo:AddItem(c)
end

items.ModelCombo:AddItem("base (Recommended - Fast & Accurate)")
items.ModelCombo:AddItem("tiny (Fastest)")
items.ModelCombo:AddItem("small (High Accuracy)")

win.On.StyleCombo.CurrentIndexChanged = function(ev)
    local idx = items.StyleCombo.CurrentIndex + 1
    local name = styles[idx] or "Hormozi Viral"
    local desc = style_descs[name] or ""
    items.StyleDesc.Text = '<small style="color:#A0A0B0;">' .. desc .. "</small>"
end

win.On.BrowseBtn.Clicked = function(ev)
    local chosen = fusion:RequestFile()
    if chosen and tostring(chosen) ~= "" then
        items.FileBox.Text = tostring(chosen)
        items.TimelineStatus.Text = '<small style="color:#10B981;">● Selected file: ' .. string.match(tostring(chosen), "[^/]+$") .. "</small>"
    end
end

win.On.CloseBtn.Clicked = function(ev)
    disp:ExitLoop()
end

win.On[winID].Close = function(ev)
    disp:ExitLoop()
end

local function refresh_live_timeline()
    local live_pm = resolve and resolve:GetProjectManager()
    local live_project = live_pm and live_pm:GetCurrentProject()
    local live_timeline = live_project and live_project:GetCurrentTimeline()
    if not live_timeline then
        items.TimelineStatus.Text = '<small style="color:#9E9EAF;">● Resolve connected - no timeline open</small>'
        return
    end

    local live_media = {}
    for _, t_type in ipairs({"video", "audio"}) do
        local count = live_timeline:GetTrackCount(t_type) or 0
        for idx = 1, count do
            for _, item in ipairs(live_timeline:GetItemListInTrack(t_type, idx) or {}) do
                local mp_item = item:GetMediaPoolItem()
                local props = mp_item and mp_item:GetClipProperty()
                local fp = props and props["File Path"]
                if fp and fp ~= "" and not live_media[fp] then
                    live_media[#live_media + 1] = fp
                    live_media[fp] = true
                end
            end
        end
    end

    items.TimelineStatus.Text = '<small style="color:#10B981;">● Live Timeline: ' .. live_timeline:GetName() .. " (" .. #live_media .. " media clips detected)</small>"
    if #live_media > 0 and items.FileBox.Text == "" then
        items.FileBox.Text = live_media[1]
    end
end

win.On.RefreshTimelineBtn.Clicked = refresh_live_timeline

win.On.ActionBtn.Clicked = function(ev)
    local media_file = items.FileBox.Text
    if not media_file or media_file == "" then
        items.StatusMsg.Text = '<span style="color:#EF4444;">Please select a media file or open a timeline with clips first!</span>'
        return
    end
    local python_file = io.open(venv_py, "rb")
    if not python_file then
        items.StatusMsg.Text = '<span style="color:#EF4444;">Python environment not found. Run the setup commands from the project README.</span>'
        return
    end
    python_file:close()

    local style_idx = items.StyleCombo.CurrentIndex + 1
    local chosen_style = styles[style_idx] or "Hormozi Viral"

    local chunk_raw = items.ChunkCombo.CurrentText
    local chunk_mode = "short"
    if string.find(chunk_raw, "1_word") then
        chunk_mode = "1_word"
    elseif string.find(chunk_raw, "balanced") then
        chunk_mode = "balanced"
    elseif string.find(chunk_raw, "sentence") then
        chunk_mode = "sentence"
    end

    local model_raw = items.ModelCombo.CurrentText
    local model_name = "base"
    if string.find(model_raw, "tiny") then
        model_name = "tiny"
    elseif string.find(model_raw, "small") then
        model_name = "small"
    end

    items.StatusMsg.Text = '<span style="color:#F3A63B;">⏳ Transcribing speech and creating captions... Please wait.</span>'
    items.ActionBtn.Enabled = false

    local cmd
    if is_windows then
        cmd = string.format(
            'start "" /B "%s" "%s" --media "%s" --style "%s" --chunk "%s" --model "%s" --auto-import',
            venv_py, quick_caption_cli, media_file, chosen_style, chunk_mode, model_name
        )
    else
        cmd = string.format(
            '"%s" "%s" --media "%s" --style "%s" --chunk "%s" --model "%s" --auto-import >/tmp/autocaption.log 2>&1 &',
            venv_py, quick_caption_cli, media_file, chosen_style, chunk_mode, model_name
        )
    end

    local result = os.execute(cmd)
    if result == nil or result == false or result == 1 then
        items.StatusMsg.Text = '<span style="color:#EF4444;">Could not start transcription. Check the Python environment setup.</span>'
        items.ActionBtn.Enabled = true
        return
    end
    items.StatusMsg.Text = '<span style="color:#F3A63B;"><b>Transcription started.</b> Captions will import into Resolve when complete.</span>'
    items.ActionBtn.Enabled = true
end

win:Show()
disp:RunLoop()
win:Hide()
