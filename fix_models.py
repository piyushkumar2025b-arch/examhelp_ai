# ============================================================
# INTEGRATION REMOVED — This file has been fully commented out.
# All external service integrations, API keys, and credentials
# have been stripped for security. Do not re-enable.
# ============================================================

# import os
# 
# directory = r"c:\Users\Piyush Kumar\Downloads\examhelp\examhelp_ai"
# 
# replacements = {
#     '"llama-3.3-70b-versatile"': '"llama-3.3-70b-versatile"',
#     "'llama-3.3-70b-versatile'": "'llama-3.3-70b-versatile'",
#     '"llama-3.1-8b-instant"': '"llama-3.1-8b-instant"',
#     "'llama-3.1-8b-instant'": "'llama-3.1-8b-instant'",
# }
# 
# for root, dirs, files in os.walk(directory):
#     for filename in files:
#         if filename.endswith(".py"):
#             filepath = os.path.join(root, filename)
#             try:
#                 with open(filepath, 'r', encoding='utf-8') as f:
#                     content = f.read()
#                 
#                 original_content = content
#                 for old_model, new_model in replacements.items():
#                     content = content.replace(old_model, new_model)
#                 
#                 if content != original_content:
#                     with open(filepath, 'w', encoding='utf-8') as f:
#                         f.write(content)
#                     print(f"Updated {filepath}")
#             except Exception as e:
#                 print(f"Failed to process {filepath}: {e}")