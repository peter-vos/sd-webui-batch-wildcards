import os
import random
import sys
import gradio as gr

from modules import scripts, script_callbacks, shared
from modules.ui_components import InputAccordion

warned_about_files = {}
repo_dir = scripts.basedir()


class WildcardsScript(scripts.Script):
    def title(self):
        return "Simple wildcards"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with InputAccordion(
            value=False,
            elem_id="wildcards_main_accordion",
            label="Wildcards",
            visible=True,
        ) as wildcards_enable:
            with gr.Row():
                wildcards_sameseed = gr.Checkbox(
                    label="Use same seed for all images",
                    value=False,
                    visible=True,
                    elem_id="wildcards_sameseed",
                )
            with gr.Row():
                with gr.Column():
                    wildcards_start_index = gr.Number(
                        label='Global start index',
                        value=0,
                        elem_id="wildcards_start_index",
                        precision=0,
                        min_width=100
                    )
                with gr.Column():
                    wildcards_length = gr.Number(
                        label='Global length',
                        value=-1,
                        elem_id="wildcards_length",
                        precision=0,
                        min_width=100
                    )
        
        components = [wildcards_enable, wildcards_sameseed, wildcards_start_index, wildcards_length]
        return components

    def replace_wildcard(self, text, seed, iter, start_index, length):
        if " " in text or len(text) == 0:
            return text
        
        isRandom = True
        if text.startswith("#"):
            isRandom = False
            text = text[1:]

        wildcards_dir = shared.cmd_opts.wildcards_dir or os.path.join(repo_dir, "wildcards")

        replacement_file = os.path.join(wildcards_dir, f"{text}.txt")
        if os.path.exists(replacement_file):
            with open(replacement_file, encoding="utf8") as f:
                lines = f.read().splitlines()
                if isRandom:
                    random.seed(seed)
                    random.shuffle(lines)

                limitedIter = iter % length if length > 0 else iter
                lineNr = start_index + limitedIter
                
                return lines[lineNr % len(lines)]
        else:
            if replacement_file not in warned_about_files:
                print(f"File {replacement_file} not found for the __{text}__ wildcard.", file=sys.stderr)
                warned_about_files[replacement_file] = 1

        return text

    def replace_prompts(self, prompts, seeds, start_index, length):
        res = []

        for i, text in enumerate(prompts):
            res.append("".join(self.replace_wildcard(chunk, seeds[i], i, start_index, length) for chunk in text.split("__")))

        return res

    def apply_wildcards(self, p, attr, infotext_suffix, start_index, length, infotext_compare=None):
        if all_original_prompts := getattr(p, attr, None):
            setattr(p, attr, self.replace_prompts(all_original_prompts, p.all_seeds, start_index, length))
            if (shared.opts.wildcards_write_infotext and all_original_prompts[0] != getattr(p, attr)[0] and
                    (not infotext_compare or p.extra_generation_params.get(f"Wildcard {infotext_compare}", None) != all_original_prompts[0])):
                p.extra_generation_params[f"Wildcard {infotext_suffix}"] = all_original_prompts[0]

    def process(self, p, wildcards_enable, wildcards_sameseed, wildcards_start_index, wildcards_length):
        if not wildcards_enable:
            return

        if wildcards_sameseed:
            seed = p.all_seeds[0]
            nr_of_seeds = len(p.all_seeds)
            p.all_seeds = []
            for i in range(nr_of_seeds):
                p.all_seeds.append(seed)

        for attr, infotext_suffix, infotext_compare in [
            ('all_prompts', 'prompt', None),
            ('all_negative_prompts', 'negative prompt', None),
            ('all_hr_prompts', 'hr prompt', 'prompt'),
            ('all_hr_negative_prompts', 'hr negative prompt', 'negative prompt'),
        ]:
            self.apply_wildcards(p, attr, infotext_suffix, wildcards_start_index, wildcards_length, infotext_compare)

        p.extra_generation_params["wildcards_enable"] = wildcards_enable
        p.extra_generation_params["wildcards_sameseed"] = wildcards_sameseed
        p.extra_generation_params["wildcards_start_index"] = wildcards_start_index
        p.extra_generation_params["wildcards_length"] = wildcards_length

def on_ui_settings():
    shared.opts.add_option("wildcards_write_infotext", shared.OptionInfo(True, "Write original prompt to infotext", section=("wildcards", "Wildcards")).info("the original prompt before __wildcards__ are applied"))


script_callbacks.on_ui_settings(on_ui_settings)
