from python_examples import count_if, sum_if, average_if


if __name__ == '__main__':
    example = list(range(10))
    print(count_if(example, ">5"))  # 4
    print(sum_if(example, "<>5"))  # 40
    print(average_if(example, "<10"))  # 4.5
