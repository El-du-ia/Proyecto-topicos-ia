from scapy.all import sniff
from cai.sdk.agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool, RunConfig
from openai import AsyncOpenAI

import asyncio
from dotenv import load_dotenv
from cai.agents.network_traffic_analyzer import network_security_analyzer_agent

load_dotenv()

@function_tool
def network_sniffer_tool(interface: str, count: int, filename: str) -> str:
    """
    Captures network packets on a specific interface and saves the summary to a text file.

    Args:
        interface: The network interface to sniff on (e.g., 'eth0', 'wlan0').
        count: The number of packets to capture.
        filename: The name of the text file to save the output (e.g., 'capture_log.txt').
    """
    try:
        print(f"[*] Starting capture on {interface} for {count} packets...")

        # Run Scapy sniff
        packets = sniff(iface=interface, count=count)

        # Process packets into a string format
        output_data = []
        for pkt in packets:
            # getting a summary line for each packet
            output_data.append(pkt.summary())

        full_content = "\n".join(output_data)

        # Save to the specified text file
        with open(filename, "w") as f:
            f.write(f"Capture Result for {interface}\n")
            f.write("-" * 30 + "\n")
            f.write(full_content)

        return f"Successfully captured {count} packets and saved details to '{filename}'."

    except PermissionError:
        return "Error: Permission denied. Scapy requires root/sudo privileges to capture packets."
    except Exception as e:
        return f"Error during capture: {str(e)}"

network_security_analyzer_agent.tools.extend([network_sniffer_tool])

original_instructions = network_security_analyzer_agent.instructions

# 2. Define a new wrapper function that handles the arguments correctly
def new_instructions(context, agent):
    # Get the original text by running the original function
    base_prompt = original_instructions(context, agent)
    # Append your custom instructions
    return base_prompt + (
        "\n\nIf the user asks to capture traffic, sniff packets, or record network activity, "
        "you MUST use the 'network_sniffer_tool'."
    )

# 3. Assign this new function back to the agent
network_security_analyzer_agent.instructions = new_instructions

async def main():
    # prompt definition
    prompt = "Capture 5 packets on interface eth0 and save them to capture.txt"
    
    print(f"Running agent with prompt: '{prompt}'")
    print("------------------------------------------------")

    # This disables tracing.
    run_config = RunConfig(tracing_disabled=True)
    result = await Runner.run(network_security_analyzer_agent, prompt, run_config=run_config)
    
    print("------------------------------------------------")
    print("Final Agent Output:")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
