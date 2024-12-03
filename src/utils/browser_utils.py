
import random
import time

from src.logging import logger


def is_scrollable(element):
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    scrollable = int(scroll_height) > int(client_height)
    logger.debug(f"Element scrollable check: scrollHeight={scroll_height}, clientHeight={client_height}, scrollable={scrollable}")
    return scrollable


def scroll_slow(driver, scrollable_element, start=0, end=3600, step=300, reverse=False):
    logger.debug(f"Starting slow scroll: start={start}, end={end}, step={step}, reverse={reverse}")

    if reverse:
        start, end = end, start
        step = -step

    if step == 0:
        logger.error("Step value cannot be zero.")
        raise ValueError("Step cannot be zero.")

    max_scroll_height = int(scrollable_element.get_attribute("scrollHeight"))
    current_scroll_position = int(float(scrollable_element.get_attribute("scrollTop")))
    logger.debug(f"Max scroll height of the element: {max_scroll_height}")
    logger.debug(f"Current scroll position: {current_scroll_position}")

    if reverse:
        if current_scroll_position < start:
            start = current_scroll_position
        logger.debug(f"Adjusted start position for upward scroll: {start}")
    else:
        if end > max_scroll_height:
            logger.warning(f"End value exceeds the scroll height. Adjusting end to {max_scroll_height}")
            end = max_scroll_height

    script_scroll_to = "arguments[0].scrollTop = arguments[1];"

    try:
        if scrollable_element.is_displayed():
            if not is_scrollable(scrollable_element):
                logger.warning("The element is not scrollable.")
                return

            if (step > 0 and start >= end) or (step < 0 and start <= end):
                logger.warning("No scrolling will occur due to incorrect start/end values.")
                return

            position = start
            previous_position = None  # Tracking the previous position to avoid duplicate scrolls
            while (step > 0 and position < end) or (step < 0 and position > end):
                if position == previous_position:
                    # Avoid re-scrolling to the same position
                    logger.debug(f"Stopping scroll as position hasn't changed: {position}")
                    break

                try:
                    driver.execute_script(script_scroll_to, scrollable_element, position)
                    logger.debug(f"Scrolled to position: {position}")
                except Exception as e:
                    logger.error(f"Error during scrolling: {e}")

                previous_position = position
                position += step

                # Decrease the step but ensure it doesn't reverse direction
                step = max(10, abs(step) - 10) * (-1 if reverse else 1)

                time.sleep(random.uniform(0.6, 1.5))

            # Ensure the final scroll position is correct
            driver.execute_script(script_scroll_to, scrollable_element, end)
            logger.debug(f"Scrolled to final position: {end}")
            time.sleep(0.5)
        else:
            logger.warning("The element is not visible.")
    except Exception as e:
        logger.error(f"Exception occurred during scrolling: {e}")

def remove_focus_active_element(driver):
    driver.execute_script("document.activeElement.blur();")
    logger.debug("Removed focus from active element.")