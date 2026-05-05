// 導出 PSD 中 'overlay-manual' 圖層為 PNG（支援多資料夾批次處理）

#target photoshop

(function () {
    // --- 第一步：循環選擇多個資料夾 ---
    var srcFolders = [];

    while (true) {
        var hint = srcFolders.length === 0
            ? "請選擇第 1 個資料夾（取消則結束）"
            : "已選 " + srcFolders.length + " 個資料夾。\n繼續選擇下一個，或按「取消」開始執行";

        var folder = Folder.selectDialog(hint);

        if (!folder) {
            break; // 使用者按取消，停止新增
        }

        // 避免重複加入同一資料夾
        var alreadyAdded = false;
        for (var k = 0; k < srcFolders.length; k++) {
            if (srcFolders[k].fsName === folder.fsName) {
                alreadyAdded = true;
                break;
            }
        }
        if (!alreadyAdded) {
            srcFolders.push(folder);
        } else {
            alert("此資料夾已加入清單，請選擇其他資料夾。");
        }
    }

    if (srcFolders.length === 0) {
        alert("未選擇任何資料夾，腳本結束。");
        return;
    }

    // --- 第二步：逐一處理每個資料夾 ---
    var totalExported = 0;
    var totalSkipped = 0;
    var summary = "";

    for (var f = 0; f < srcFolders.length; f++) {
        var srcFolder = srcFolders[f];

        // 在每個資料夾下建立 inpainted 子資料夾
        var outFolder = new Folder(srcFolder.fsName + "/inpainted");
        if (!outFolder.exists) {
            outFolder.create();
        }

        var psdFiles = srcFolder.getFiles(/\.psd$/i);
        if (psdFiles.length === 0) {
            summary += "[" + srcFolder.name + "] 沒有 PSD 檔案，已跳過\n";
            continue;
        }

        var folderExported = 0;
        var folderSkipped = 0;

        for (var i = 0; i < psdFiles.length; i++) {
            var psdFile = psdFiles[i];
            var doc = null;

            try {
                doc = app.open(psdFile);

                var targetLayer = findLayerByName(doc, "overlay-manual");

                if (targetLayer !== null) {
                    setAllLayersVisibility(doc, false);
                    targetLayer.visible = true;

                    var pngOptions = new PNGSaveOptions();
                    pngOptions.compression = 0;
                    pngOptions.interlaced = false;

                    var baseName = psdFile.name.replace(/\.psd$/i, "");
                    var outFile = new File(outFolder.fsName + "/" + baseName + ".png");

                    doc.saveAs(outFile, pngOptions, true, Extension.LOWERCASE);
                    folderExported++;
                } else {
                    folderSkipped++;
                }
            } catch (e) {
                alert("處理檔案時發生錯誤：" + psdFile.name + "\n" + e.message);
            } finally {
                if (doc !== null) {
                    doc.close(SaveOptions.DONOTSAVECHANGES);
                }
            }
        }

        totalExported += folderExported;
        totalSkipped += folderSkipped;
        summary += "[" + srcFolder.name + "] 導出 " + folderExported + " 個，跳過 " + folderSkipped + " 個\n";
    }

    alert(
        "全部完成！\n\n" +
        summary +
        "\n合計導出：" + totalExported + " 個\n" +
        "合計跳過：" + totalSkipped + " 個"
    );
})();

/**
 * 遞歸在文件中尋找指定名稱的圖層
 * @param {Document|LayerSet} container
 * @param {string} name
 * @returns {Layer|null}
 */
function findLayerByName(container, name) {
    var layers = container.layers;
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        if (layer.name === name) {
            return layer;
        }
        if (layer.typename === "LayerSet") {
            var found = findLayerByName(layer, name);
            if (found !== null) {
                return found;
            }
        }
    }
    return null;
}

/**
 * 設定文件中所有頂層圖層的可見性
 * @param {Document} doc
 * @param {boolean} visible
 */
function setAllLayersVisibility(doc, visible) {
    var layers = doc.layers;
    for (var i = 0; i < layers.length; i++) {
        layers[i].visible = visible;
    }
}
