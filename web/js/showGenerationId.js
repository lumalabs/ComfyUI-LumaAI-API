//Based on https://github.com/pythongosssss/ComfyUI-Custom-Scripts/blob/main/web/js/showText.js

import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

// Displays input text on a node
app.registerExtension({
    name: "lumaai.showgenerationid",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name == "LumaText2Video"
            || nodeData.name == "LumaImage2Video"
            || nodeData.name == "LumaInterpolateGenerations"
            || nodeData.name == "LumaExtendGeneration"
            || nodeData.name == "LumaImageGeneration"
            || nodeData.name == "LumaModifyImage"
        ) {
            function populate(text) {
                const v = [...text];
                if (this.widgets) {
                    if (this.widgets[this.widgets.length - 1].name == "filename") {
                        const w = ComfyWidgets["STRING"](this, "gen_output", ["STRING", { multiline: true }], app).widget;
                        w.inputEl.readOnly = true;
                        w.inputEl.style.opacity = 0.6;
                        w.value = v[0];
                        this.widgets.push(w);
                    } else {
                        this.widgets[this.widgets.length - 1].value = v[0];
                    }
                }

                requestAnimationFrame(() => {
                    const sz = this.computeSize();
                    if (sz[0] < this.size[0]) {
                        sz[0] = this.size[0];
                    }
                    if (sz[1] < this.size[1]) {
                        sz[1] = this.size[1];
                    }
                    this.onResize?.(sz);
                    app.graph.setDirtyCanvas(true, true);
                });
            }

            // When the node is executed we will be sent the input text, display this in the widget
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                populate.call(this, message.text);
            };

            const onExecutionStart = nodeType.prototype.onExecutionStart;
            nodeType.prototype.onExecutionStart = function () {
                onExecutionStart?.apply(this, arguments);
                populate.call(this, ["generating..."]);
            };
        }
    },
});
