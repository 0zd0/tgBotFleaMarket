def format_price(price: int, separator: str = ' '):
    formatted_price = "{:,}".format(price)
    formatted_price = formatted_price.replace(',', separator)
    return formatted_price
