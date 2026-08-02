"""
<MODULE_CONTRACT>
  <ID>M-1</ID>
  <PURPOSE>Точка входа проекта. Демонстрация паттерна GRACE: контракт -> код.</PURPOSE>
  <SCOPE>Обеспечивает простую проверку работоспособности окружения. НЕ выполняет бизнес-логику анализа неравенства.</SCOPE>
  <INPUTS>Отсутствуют. Функция add(a, b) принимает два числа.</INPUTS>
  <OUTPUTS>Целочисленный результат сложения add(a, b) или строку с приветствием.</OUTPUTS>
  <ERRORS>TypeError при передаче нечисловых аргументов в add().</ERRORS>
  <INVARIANTS>add(a, b) == add(b, a) для любых чисел.</INVARIANTS>
  <DEPENDENCIES>Нет.</DEPENDENCIES>
</MODULE_CONTRACT>
"""


# START: greeting
def hello() -> str:
    """Возвращает приветственное сообщение проекта."""
    return "Inequality study: GRACE skeleton ready."


# END: greeting


# START: arithmetic
def add(a: int, b: int) -> int:
    """Складывает два числа."""
    return a + b


# END: arithmetic
