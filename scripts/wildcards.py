from functools import cache
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
                wildcards_write_infotext = gr.Checkbox(
                    label="Write infotext",
                    value=False,
                    visible=True,
                    elem_id="wildcards_write_infotext",
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
                        label='Global length; -1 = no limit',
                        value=-1,
                        elem_id="wildcards_length",
                        precision=0,
                        min_width=100
                    )
            with gr.Row():
                with gr.Column():
                    wildcards_repeat_replace = gr.Number(
                        label='Repeat replace value # iterations',
                        value=1,
                        elem_id="wildcards_repeat_replace",
                        precision=0,
                        min_width=100
                    )
                with gr.Column():
                    wildcards_repeat_seed = gr.Number(
                        label='Repeat seeds every # iterations; -1 = do not repeat',
                        value=-1,
                        elem_id="wildcards_repeat_seed",
                        precision=0,
                        min_width=100
                    )
        
        components = [wildcards_enable, wildcards_write_infotext, wildcards_start_index, wildcards_length, wildcards_repeat_replace, wildcards_repeat_seed]
        return components

    def replace_wildcard(self, text, seed, iter):
        if " " in text or len(text) == 0:
            return text

        isRandom = True
        if text.startswith("#"):
            isRandom = False
            text = text[1:]

        if text in self.cache:
            lines = self.cache[text]
        else:
            wildcards_dir = shared.cmd_opts.wildcards_dir or os.path.join(repo_dir, "wildcards")

            replacement_file = os.path.join(wildcards_dir, f"{text}.txt")
            if os.path.exists(replacement_file):
                with open(replacement_file, encoding="utf8") as f:
                    lines = f.read().splitlines()
                    if isRandom:
                        random.seed(seed)
                        random.shuffle(lines)
                        # Shuffle once before storing to prevent doubles
                        self.cache[text] = lines
            else:
                if replacement_file not in warned_about_files:
                    print(f"File {replacement_file} not found for the __{text}__ wildcard.", file=sys.stderr)
                    warned_about_files[replacement_file] = 1

        if not lines:
            return text

        repeatedIter = iter // self.repeat_replace if self.repeat_replace > 1 else iter
        limitedIter = repeatedIter % self.length if self.length > 0 else repeatedIter
        lineNr = self.start_index + limitedIter
                
        return lines[lineNr % len(lines)]

    def replace_prompts(self, prompts, seeds):
        res = []

        for i, text in enumerate(prompts):
            res.append("".join(self.replace_wildcard(chunk, seeds[i], i) for chunk in text.split("__")))

        return res

    def apply_wildcards(self, p, attr, infotext_suffix, infotext_compare=None):
        if all_original_prompts := getattr(p, attr, None):
            setattr(p, attr, self.replace_prompts(all_original_prompts, p.all_seeds))
            if (self.write_infotext and all_original_prompts[0] != getattr(p, attr)[0] and
                    (not infotext_compare or p.extra_generation_params.get(f"Wildcard {infotext_compare}", None) != all_original_prompts[0])):
                p.extra_generation_params[f"Wildcard {infotext_suffix}"] = all_original_prompts[0]

    def process(self, p, wildcards_enable, wildcards_write_infotext, wildcards_start_index, wildcards_length, wildcards_repeat_replace, wildcards_repeat_seed):
        if not wildcards_enable:
            return

        self.cache = dict()
        self.start_index = wildcards_start_index
        self.length = wildcards_length
        self.repeat_replace = wildcards_repeat_replace
        self.write_infotext = wildcards_write_infotext
        
        if wildcards_repeat_seed > 0:
            nr_of_seeds = len(p.all_seeds)
            if nr_of_seeds > wildcards_repeat_seed:
                seeds_subset = p.all_seeds[:wildcards_repeat_seed]
                p.all_seeds = seeds_subset[:]
                while len(p.all_seeds) < nr_of_seeds:
                    p.all_seeds.extend(seeds_subset)
                else:
                    p.all_seeds = p.all_seeds[:nr_of_seeds]
        
        if wildcards_write_infotext:
            p.extra_generation_params["wildcards_enable"] = wildcards_enable
            p.extra_generation_params["wildcards_write_infotext"] = wildcards_write_infotext
            p.extra_generation_params["wildcards_start_index"] = wildcards_start_index
            p.extra_generation_params["wildcards_length"] = wildcards_length
            p.extra_generation_params["wildcards_repeat_replace"] = wildcards_repeat_replace
            p.extra_generation_params["wildcards_repeat_seed"] = wildcards_repeat_seed

        for attr, infotext_suffix, infotext_compare in [
            ('all_prompts', 'prompt', None),
            ('all_negative_prompts', 'negative prompt', None),
            ('all_hr_prompts', 'hr prompt', 'prompt'),
            ('all_hr_negative_prompts', 'hr negative prompt', 'negative prompt'),
        ]:
            self.apply_wildcards(p, attr, infotext_suffix, infotext_compare)
