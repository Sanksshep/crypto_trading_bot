import json
import logging
from main import main

logging.basicConfig(filename='bot.log', level=logging.INFO)

def test_in_sandbox():
    """
    Test the trading bot in Coinbase's sandbox environment.
    """
    logging.info("Starting sandbox test")
    
    config_path = 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    config['sandbox_mode'] = True
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    logging.info("Running main trading bot in sandbox mode")
    main()

if __name__ == "__main__":
    test_in_sandbox()
