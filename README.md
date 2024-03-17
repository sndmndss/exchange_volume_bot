## Installation

To install the trading bot, follow these steps:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trading-bot.git
```
   
2. Navigate to the project directory:
``` bash
cd trading-bot
  ```

3. Create environment:
```
python -m venv venv
```
4. Activate environment:

_On windows_
```
venv\Scripts\activate
```
_On linux or Mac OS:_
```
source venv/bin/activate
```
5. Install packages:
```bash
pip install requirements.txt
```
## Configuration

1. Add your public and private keys to the data/public_keys.txt and data/private_keys.txt files respectively, one key per line.
```
# data/public_keys.txt
your_public_key_1
your_public_key_2
```
```
# data/private_keys.txt
your_private_key_1
your_private_key_2
```
IMPORTANT:
**Quantity of public keys, private keys and proxies must be equal, without it code won't work**
2. Add proxy to the data/proxies.txt file in the format host:port:username:password, one proxy per line.

## Usage

**To run the trading bot, execute the following command from the project directory:**

```bash
python main.py
```

Follow the on-screen prompts to configure the trading parameters such as the trading symbol, contract format, and quantity spread.


Remember, that you can access additional configuration options by entering 000 when prompted to choose a trading symbol. 

**To stop the bot you need to press Ctrl+C or close the terminal**

## Troubleshooting

Second function of extra options works only sometimes because backpack api works not correctly.

**If you have questions, problems or offer contact me in telegram: [@sndmnds](https://t.me/sndmnds)**
